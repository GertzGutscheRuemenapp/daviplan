import pandas as pd
import os
from datentool.settings_local import DATABASES

def main():
    folder = r'E:\tmp'
    fn = os.path.join(folder, 'datentool_tables.xlsx')
    DB = DATABASES['default']
    conn_str = f'postgresql+psycopg2://{DB["USER"]}:{DB["PASSWORD"]}@{DB["HOST"]}:{DB["PORT"]}/{DB["NAME"]}'
    table_name = 'django_content_type'
    df_meta = pd.read_sql_table(table_name, conn_str)
    date_columns = ['last_login', 'date_joined']

    with pd.ExcelWriter(fn, engine='xlsxwriter') as writer:
        for row in df_meta.itertuples():
            table_name = f'{row.app_label}_{row.model}'
            try:
                df = pd.read_sql_table(table_name, conn_str)
            except ValueError:
                continue
            for date_column in date_columns:
                if date_column in df:
                    df[date_column] = df[date_column].apply(lambda a: pd.to_datetime(a).date)
            df.to_excel(writer, sheet_name=row.model)



if __name__ == '__main__':
    main()
