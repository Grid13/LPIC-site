import json
import pymysql
import logging
import configparser
import hashlib
import os
import shutil
from difflib import SequenceMatcher

class Orchestrateur():

    def __init__(self) -> None:
        self.config = self.get_config()
        logging.basicConfig(filename=f"log/6df482bf-de9a-4d2a-b55b-15ec92ea60c0.log",
                        format='%(asctime)s %(message)s',
                        filemode='a',
						level=logging.INFO)
        self.logger = logging.getLogger()
        db 			= self.config["database"]
        connection 	= pymysql.connect(host = db["host"], user = db["user"], db = db["db"] , password = db["pwd"], autocommit = 1)
        self.cur 	= connection.cursor()

    def get_config(self) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config.read("configuration.conf")
        return config

    def convertResultFetchallToListOfDict(self, data, keys):
        return [{keys[column] : row[column] if "date" not in keys[column] else row[column].timestamp() for column in range(len(row))} for row in data]

    def get_all_exercice(self):
        result = {}
        self.cur.execute("SELECT e.titre, e.id, l.langage FROM exercice e JOIN langage l ON e.langage = l.id")
        all_exercice_brut = self.convertResultFetchallToListOfDict(self.cur.fetchall(), ["titre", "value", "langage"])
        for exercice in all_exercice_brut:
            if exercice["langage"] not in result:
                result[exercice["langage"]] = []
            result[exercice["langage"]].append({"titre" : exercice["titre"], "value" : exercice["value"]})
        return result

    def all_mark_from_user(self, user_id : int):
        self.cur.execute("SELECT e.titre, r.mark, u.name, l.langage FROM render r JOIN user u ON u.id = r.user JOIN exercice e ON e.id = r.exercice JOIN langage l ON l.ID = e.langage where u.UUID = %s order by e.titre asc, r.mark desc", user_id)
        return self.convertResultFetchallToListOfDict(self.cur.fetchall(), ["exo", "mark", "user", "langage"])

    def best_mark_by_exercice(self):
        self.cur.execute("SELECT e.titre, max(r.mark), u.name, l.langage FROM render r JOIN user u ON u.id = r.user JOIN exercice e ON e.id = r.exercice JOIN langage l ON l.ID = e.langage GROUP BY e.id")
        return self.convertResultFetchallToListOfDict(self.cur.fetchall(), ["exo", "mark", "user", "langage"])

    def get_all_project(self):
        self.cur.execute("SELECT e.titre, e.description, e.attent, l.langage FROM exercice e JOIN langage l ON e.langage = l.id")
        return self.convertResultFetchallToListOfDict(self.cur.fetchall(), ["titre", "description", "attent", "langage"])

    def if_login(self, dict):
        return self.cur.execute("SELECT * from user where pwd = %s and UUID = %s", (hashlib.md5(dict["pwd"].encode()).hexdigest(), dict["uuid"]))

    def get_user(self, pwd, uuid):
        self.cur.execute("SELECT id from user where pwd = %s and UUID = %s", (hashlib.md5(pwd.encode()).hexdigest(), uuid))
        return self.cur.fetchall()[0][0]

    def get_exercice(self, id_exo):
        self.cur.execute("SELECT attent, correction from exercice where id=%s", (id_exo))
        return self.convertResultFetchallToListOfDict(self.cur.fetchall(), ["attent", "correction"])[0]

    def lunch_correction(self, json, extension):
        self.logger.info(f'lancement de notation pour {json} avec un fichier de type {extension}')
        mark = None
        if extension == "py":
            #os.system('python upload' + "/" + json["uuidMake"] + "/" + json["uuidMake"] +".py")
            os.system("./python.sh")
        elif extension == "c":
            os.system("./c.sh")
        else:
            return False
        witness_exercice = self.get_exercice(json["nb_exo"])
        try:
            with open("upload" + "/" + json["uuidMake"] + "/result.txt", "r") as f:
                attent_render = "".join(f.readlines())
        except Exception:
            mark = 0
            attent_render = ""
        try:
            with open("upload" + "/" + json["uuidMake"] + "/" + json["uuidMake"] + "." + extension, "r") as f:
                file_render = "".join(f.readlines())
        except Exception:
            mark = 0
            file_render = ""
        if not mark:
            coeff_result = SequenceMatcher(None, witness_exercice["attent"], attent_render).ratio()
            coeff_file = SequenceMatcher(None, witness_exercice["correction"], file_render).ratio()
            mark = 50*coeff_result + 50*coeff_file
        self.logger.info('5')
        self.cur.execute("INSERT INTO `render`(`user`, `exercice`, `mark`) VALUES (%s, %s, %s);", (self.get_user(json["pwd"], json["uuid"]), json["nb_exo"], mark))
        shutil.rmtree("upload" + "/" + json["uuidMake"])
        return True

if __name__ == "__main__":
    o = Orchestrateur()
    print(o.all_mark_from_user(111111))
    print(o.best_mark_by_exercice())
    print(o.get_all_exercice())
    print(o.get_all_project())