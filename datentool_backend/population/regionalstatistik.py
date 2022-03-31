import pandas as pd
import requests
from io import StringIO


class GenesisAPI():

    def __init__(self, url, language='de', username=None, password=None):
        self.url = url
        self.username = username
        self.password = password
        self.language = language

    def get_params(self):
        params = {
            'language': self.language,
        }
        if self.username:
            params['username'] = self.username
        if self.password:
            params['password'] = self.password
        return params

    def find(self, search_term: str, category: str='all') -> dict:
        '''
        query "find"-route of Genesis API to get tables fitting the search term
        returns the response as JSON
        '''
        print(f'Querying search term "{search_term}" in category "{category}"')
        params = self.get_params()
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
            raise ConnectionError('API is not responding.')
        jres = res.json()
        if res.status_code != 200:
            msg = jres['Status']['Content']
            raise Exception(f'API responded: {msg}')
        return jres

    def query_table(self, code: str, ags=[],
                    start_year=1900, end_year=2100) -> str:
        '''
        query "tablefile"-route to retrieve a flat csv with the data of the
        table according to the code
        '''
        url = f'{self.url}/data/tablefile'
        params = self.get_params()
        params['regionalkey'] = ','.join(ags)
        params['name'] = code
        params['area'] = 'all'
        params['format'] = 'ffcsv'
        params['startyear'] = start_year
        params['endyear'] = end_year
        try:
            res = requests.get(url, params=params)
        except ConnectionError:
            raise ConnectionError('API is not responding. Try again later')
        if res.status_code != 200:
            jres = res.json()
            raise Exception(jres['Status']['Content'])
        return res.text


class Regionalstatistik(GenesisAPI):
    URL = f'https://www.regionalstatistik.de/genesisws/rest/2020'
    POP_CODE = '12411-02-03-5'

    def __init__(self, username=None, password=None,
                 start_year=1900, end_year=2100):
        super().__init__(self.URL, username=username, password=password)
        self.start_year = start_year
        self.end_year = end_year

    def query_population(self, ags=[]) -> pd.DataFrame:
        '''
        columns of dataframe:
        year - year
        AGS - AGS of the area
        GES - GESW(=female) | GESM(=male) | NaN(=both)
        ALTX20 - Age group code (NaN = sum over groups)
        value - number of inhabitants
        '''
        fftxt = self.query_table(self.POP_CODE, ags=ags,
                                 start_year=self.start_year,
                                 end_year=self.end_year)
        df = pd.read_csv(StringIO(fftxt), delimiter=';', decimal=",", dtype='str')
        code_columns = [c for c in df.columns.values
                        if c.endswith('Merkmal_Code')]
        pop_df = pd.DataFrame()
        # ToDo: actually it is "Stichtag" 31.12. of this year, so +1?
        pop_df['year'] = df['Zeit'].apply(lambda y: y.split('.')[-1])
        for column in code_columns:
            i = column.split('_')[0]
            col_name = df[column].unique()[0]
            pop_df[col_name] = df[f'{i}_Auspraegung_Code']
        values = df['BEVSTD__Bevoelkerungsstand__Anzahl']
        values[values=='-'] = 0
        pop_df['value'] = values.astype('int')
        pop_df.rename(columns={'GEMEIN': 'AGS'}, inplace=True)
        return pop_df
