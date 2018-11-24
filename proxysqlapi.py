import datetime
from datetime import datetime
import MySQLdb
import kayvee
import logging
import yaml
import tornado.web


MYSQL_CONFIG = {
    'Host': 'localhost',
    'Port': 3306,
    'User': 'monitor',
    'Password': 'monitor',
    'Db': '',
}

PROXY_CONFIG = {
    'Status': '',
}


class MysqlManager:
    @staticmethod
    def set_mysql_config():
        """
        Read config.yml and setting variables
        """
        try:
            stream = open("config.yml", "r")
            docs = yaml.load_all(stream)
            for doc in docs:
                MYSQL_CONFIG["Host"] = doc['mysql']["host"]
                MYSQL_CONFIG["Port"] = doc['mysql']["port"]
                MYSQL_CONFIG["User"] = doc['mysql']["user"]
                MYSQL_CONFIG["Password"] = doc['mysql']["password"]
                MYSQL_CONFIG["Db"] = doc['mysql']["db"]

                logging.debug(kayvee.formatLog("Set_mysql_config", "debug", "creating Set_mysql_config",
                                               {'context': "set_mysql_config Successfull",
                                                'time': str(datetime.now())}))

        except Exception as e:
            logging.error(kayvee.formatLog("Set_mysql_config", "error", "creating Set_mysql_config",
                                           {'context': "set_mysql_config param not found: " + str(e),
                                            'time': str(datetime.now())}))

    def get_mysql_conn(self):
        """
        Read Database parameters from variables and create database connection object
        :return: MySQLdb
        """

        logging.debug(kayvee.formatLog("get_mysql_conn", "debug", "Starting ....",
                                       {'context': "Create mysql conn", 'time': str(datetime.now())}))
        self.set_mysql_config()

        try:
            return MySQLdb.connect(
                host=MYSQL_CONFIG['Host'],
                port=MYSQL_CONFIG["Port"],
                passwd=MYSQL_CONFIG["Password"],
                db=MYSQL_CONFIG["Db"],
                user=MYSQL_CONFIG["User"]
            )

        except Exception as e:
            logging.error(kayvee.formatLog("get_mysql_conn", "error", "Error!",
                                           {'context': "Error get_mysql_conn: " + str(e), 'time': str(datetime.now())}))

    @staticmethod
    def mysql_query(conn, query):
        """
        Wrapper to connect to the database returning certain query value
        :param conn:
        :param query:
        :return: cur
        """

        logging.debug(kayvee.formatLog("mysql_query", "debug", "Starting...",
                                      {'context': "Wrapper for query:" + str(query), 'time': str(datetime.now())}))
        try:
            cur = conn.cursor(MySQLdb.cursors.DictCursor)
            cur.execute(query)
            return cur
        except Exception as e:
            logging.debur(kayvee.formatLog("mysql_query", "error", "Error on mysql_query",
                                           {'context': " Error:" + str(e), 'time': str(datetime.now())}))
            return None

    def __init__(self):
        self.set_mysql_config()


class ProxyManager:

    @staticmethod
    def set_proxy_config():
        """
        Read config.yml and setting variables
        """
        try:
            stream = open("config.yml", "r")
            docs = yaml.load_all(stream)
            for doc in docs:
                PROXY_CONFIG["Status"] = doc['proxy']["status"]
                logging.debug(kayvee.formatLog("ProxyManager", "debug", "creating Set_proxy_config",
                                               {'context': "set_proxy_config Successfull",
                                                'time': str(datetime.now())}))

        except Exception as e:
            logging.error(kayvee.formatLog("ProxyManager", "error", "creating Set_proxy_config",
                                           {'context': "set_proxy_config param not found: " + str(e),
                                            'time': str(datetime.now())}))

    @staticmethod
    def check_instance(instance):
        mm = MysqlManager()
        conn = mm.get_mysql_conn()
        result = ''
        query = "select status from  mysql_server where hostname=  '%s'" % instance
        try:
            cur = MysqlManager.mysql_query(conn, query)
            result_set = cur.fetchall()
            if result_set:
                for row in result_set:
                    result = row["status"]
                    logging.info(kayvee.formatLog("ProxyManager", "info", "check_instance",
                                                  {'context': "Check Instance: " + str(result),
                                                   'time': str(datetime.now())}))
            else:
                logging.info(kayvee.formatLog("ProxyManager", "info", "check_instance",
                                               {'context': "No data returned for: " + str(instance),
                                                'time': str(datetime.now())}))


        except Exception as e:
            logging.error(kayvee.formatLog("ProxyManager", "error", "check_instance",
                                      {'context': "Error: " + str(result), 'time': str(datetime.now())}))

        finally:
            cur.close()
            conn.close()
            return result

    @staticmethod
    def change_instance(args, proxymanagercls):
        """

        """
        mm = MysqlManager()
        conn = mm.get_mysql_conn()
        return_value = False
        status = args.get("status")
        instance = args.get("hostname")
        result = proxymanagercls.check_instance(instance)
        try:
            if status != result:
                if status in PROXY_CONFIG["Status"]:
                    query = "update mysql_server set status = '%s' where hostname= '%s' " % (status, instance)
                    cur = MysqlManager.mysql_query(conn, query)
                    conn.commit()
                    cur.close()
                    return_value = True
                    logging.info(kayvee.formatLog("ProxyManager", "info", "change_instance",
                                                  {'context': "Update successfully new status: "
                                                              + str(status), 'time': str(datetime.now())}))
                else:
                    logging.info(kayvee.formatLog("ProxyManager", "info", "change_instance",
                                                  {'context': "This is not a valid parameter: "
                                                              + str(status), 'time': str(datetime.now())}))
            else:
                logging.info(kayvee.formatLog("ProxyManager", "info", "change_instance",
                                              {'context': "Host already with status: "
                                                          + str(status), 'time': str(datetime.now())}))
        except Exception as e:
            logging.error(kayvee.formatLog("ProxyManager", "error", "change_instance",
                                           {'context': "Error: " + str(e), 'time': str(datetime.now())}))
        finally:
            conn.close()
            return return_value

    def __init__(self):
        self.set_proxy_config()


class StatusHandler(tornado.web.RequestHandler):
    def get(self, database):
        pm = ProxyManager()
        instance = database
        r = pm.check_instance(instance)
        if r:
            logging.info(kayvee.formatLog("StatusHandler", "info", "get",
                                          {'context': "Checking instance: "
                                                      + str(r), 'time': str(datetime.now())}))
        self.write('Done')

    def post(self, database):
        logging.info(kayvee.formatLog("StatusHandler", "info", "post",
                                      {'context': "Post: " + str(database), 'time': str(datetime.now())}))
        pm = ProxyManager()
        data = tornado.escape.json_decode(self.request.body)
        pm.change_instance(data, pm)
        self.write('Done')


app = tornado.web.Application([
    (r"/status/(.*)", StatusHandler,)
    ])


if __name__ == "__main__":
    logging.basicConfig(filename='/tmp/proxysqlapi.log', level=logging.INFO)
    app.listen(6632)
    tornado.ioloop.IOLoop.current().start()

