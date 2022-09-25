#!/usr/bin/python3

import datetime

from muglebase.constants.MysqlConstants import MysqlConstants
from muglebase.dbaccess import database
from muglebase.dbaccess.database import database_details
from muglebase.model.pool_utxo import Pool_utxo
from muglebase.model.mugle_stats import Mugle_stats

from muglelib import lib


if __name__ == '__main__':
    database = lib.get_db()

#    for i in range(0,10):
#        tmp = Pool_utxo(id=str(i), address=str(i), amount=1.5*i)
#        database.db.createDataObj(tmp)


#    utxo = Pool_utxo.getPayable(0)[0]
#    print(utxo)
#    locked_utxo = Pool_utxo.get_locked_by_id(utxo.id)
#    print(locked_utxo)
#    locked_utxo.amount=1.0
#    database.db.getSession().begin_nested();
#    locked_utxo.amount=7.0
#    database.db.getSession().commit()
#    database.db.getSession().commit()
#
#    utxo = Pool_utxo.getPayable(0)[0]
#    print(utxo)


#    for utxo in Pool_utxo.getPayable(0):
#        Pool_utxo.get_locked_by_id(utxo.id)
#        print(utxo)

    dt = datetime.datetime.utcnow()
    print(dt)
#    new_gs = Mugle_stats(timestamp=dt, height=1, gps=10, difficulty=29, total_utxoset_size=0, total_transactions=0)
#    print(new_gs)
#    duplicate = database.db.createDataObj_ignore_duplicates(new_gs)
#    database.db.getSession().commit()

    for gs in Mugle_stats.get_last_n(10):
      print(gs)

    

