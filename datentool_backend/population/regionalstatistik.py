class Regionalstatistik():

    def __init__(self):
        pass




class Destatis(DBApp):
    """
    search and retrieve data tables from Destatis API and write them to
    target database
    """
    schema = 'destatis'
    url = f'https://www-genesis.destatis.de/genesisWS/rest/2020'
    sub_folder = 'destatis'
    params = {
        'language': 'de',
        'username': '',
        'password': ''
    }
    special_chars = 'äüö!@#$%^&*()[]{};:,./<>?\|`~=+"\' '
    tablename_length = 63
    ags_foreign_table = 'verwaltungsgrenzen.krs_2019_12'

    def __init__(self, database: str, **kwargs):
        super().__init__(schema=self.schema, **kwargs)
        self.database = database
        self.set_login(database=database)
        sql = f'''
        CREATE SCHEMA IF NOT EXISTS {self.schema};
        '''
        with Connection(login=self.login) as conn:
            self.run_query(sql, conn=conn, verbose=False)
        self.check_platform()

    def find(self, search_term: str, category: str='all') -> dict:
        '''
        query "find"-route of Destatis API to get tables fitting the search term
        returns the response as JSON
        '''
        self.logger.info(f'Querying search term "{search_term}" in '
                         f'category "{category}"')
        params = self.params.copy()
        params['term'] = search_term
        params['category'] = category
        url = f'{self.url}/find/find'
        retries = 0
        res = None
        while retries < 3:
            try:
                res = requests.get(url, params=params)
                break
            except ConnectionError:
                retries += 1
        if not res:
            raise ConnectionError('Destatis is not responding.')
        jres = res.json()
        if res.status_code != 200:
            msg = jres['Status']['Content']
            self.logger.error(f'Destatis responded: {msg}. Skipping...')
            return
        return jres

    def query_table(self, code: str, ags=[]) -> pd.DataFrame:
        '''
        query "tablefile"-route to retrieve a flat csv with the data of the
        table according to the code
        '''
        url = f'{self.url}/data/tablefile'
        params = self.params.copy()
        params['regionalkey'] = ','.join(ags)
        params['name'] = code
        params['area'] = 'all'
        params['format'] = 'ffcsv'
        try:
            res = requests.get(url, params=params)
        except ConnectionError:
            raise ConnectionError('Destatis is not responding. Try again later')
        if res.status_code != 200:
            jres = res.json()
            self.logger.error(jres['Status']['Content'])
            return
        return pd.read_csv(StringIO(res.text), delimiter=';', decimal=",")

    def add_table_codes(self, search_term: str):
        '''
        find and add Destatis table codes and their descriptions to the database
        matching the given search term
        '''
        with Connection(login=self.login) as conn:
            sql = f'''
            CREATE TABLE IF NOT EXISTS {self.schema}.table_codes (
            code varchar(20) PRIMARY KEY,
            content varchar(256) NOT NULL,
            tablename varchar({self.tablename_length}) NOT NULL
            )
            '''
            self.run_query(sql, conn=conn, verbose=False)
            res = self.find(search_term.strip(), category='tables')
            if not res:
                return
            tables = res['Tables'] or []
            self.logger.info(f'Found {len(tables)} tables.')
            rem = {ord(c): "" for c in self.special_chars}
            for table in tables:
                code = table['Code']
                content = table['Content'][:256].replace('\n', ' ')
                table_name = f'{code}_{content.lower()}'.translate(rem)
                table_name = table_name[:self.tablename_length]
                sql = f'''
                INSERT INTO {self.schema}.table_codes
                (code, content, tablename)
                VALUES ('{code}','{content}','{table_name}')
                ON CONFLICT (code)
                DO
                UPDATE SET content='{content}', tablename='{table_name}';
                '''
                self.run_query(sql, conn=conn, verbose=False)

    def get_tables(self) -> list:
        '''
        request all previously found table codes from database
        '''
        sql = f'SELECT * FROM {self.schema}.table_codes ORDER BY code ASC;'
        with Connection(login=self.login) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(sql)
            except UndefinedTable:
                return []
            rows = cursor.fetchall()
            return rows

    def download_table(self, code: str, geom: 'ogr.Geometry', source_db: str):
        '''
        download data table according to given code from Destatis API and store
        it in the project folder and in the database;
        existing data with same code is overwritten
        '''
        foreign_login = get_foreign_login(source_db)

        wkt = geom.ExportToWkt()
        s_ref = geom.GetSpatialReference()
        srid = s_ref.GetAuthorityCode(None) if s_ref else '4326'
        sql = f'''
        SELECT ags FROM {self.ags_foreign_table}
        WHERE
        ST_Intersects(ST_GeomFromEWKT('SRID={srid};{wkt}'), geom)
        '''

        project_folder = os.path.join(self.database,
                                      self.sub_folder)
        folder = os.path.join(self.folder, 'projekte', project_folder)
        self.make_folder(folder)
        with Connection(login=foreign_login) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            ags = [r.ags for r in rows]

        #table_df = None
        # request every single AGS, API is aggregating results otherwise
        table_df = self.query_table(code, ags=ags)
        table_df = table_df.drop(columns=[c for c in table_df.columns
                                          if c.endswith('_Code')])
        fn = f'{code}.csv'
        fp = os.path.join(folder, fn)
        self.logger.info(f'Writing data to {os.path.join(project_folder, fn)}')
        try:
            table_df.to_csv(fp, decimal=',', sep=';')
        except PermissionError:
            self.logger.error("Can't write to file. Maybe it is opened. "
                              "Skipping...")

        sql = f'''
        SELECT tablename FROM {self.schema}.table_codes
        WHERE code = '{code}';
        '''
        with Connection(login=self.login) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            row = cursor.fetchone()
            tn = code if not row else row.tablename
            self.logger.info(f'Writing data to table {self.schema}.{tn}')
            col_def = []
            for name, dtype in zip(table_df.columns, table_df.dtypes):
                if np.issubdtype(dtype, np.integer):
                    sql_type = 'INTEGER'
                elif np.issubdtype(dtype, np.float):
                    sql_type = 'DOUBLE PRECISION'
                else:
                    sql_type = 'TEXT'
                    #table_df[name] = table_df[name].apply(lambda x: f"'{x}'")
                col_def.append(f'"{name}" {sql_type}')
            vals = [str(tuple(row.values)) for idx, row in table_df.iterrows()]
            cols = [f'"{c}"' for c in table_df.columns]
            sql = f'''
            DROP TABLE IF EXISTS {self.schema}."{tn}" CASCADE;
            CREATE TABLE {self.schema}."{tn}" (
            {','.join(col_def)}
            );
            INSERT INTO {self.schema}."{tn}" ({','.join(cols)})
            VALUES
            {','.join(vals)}
            '''
            cursor.execute(sql)