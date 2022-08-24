if __name__ == '__main__':

    import pandas as pd
    from django.db import connection

    df_demand = pd.read_sql_query(q_demand, connection, params=p_demand)
    df_cp = pd.read_sql_query(q_cp, connection, params=p_cp)
    df_areas = pd.read_sql_query(q_areas, connection, params=p_areas)
    df_acells = pd.read_sql_query(q_acells, connection, params=p_acells)

    df_drs = pd.read_sql_query(q_drs, connection, params=p_drs)
    df_pop = pd.read_sql_query(q_pop, connection, params=p_pop)
    df_rcp = pd.read_sql_query(q_rcp, connection, params=p_rcp)

    df_query = pd.read_sql_query(query, connection, params=params)
