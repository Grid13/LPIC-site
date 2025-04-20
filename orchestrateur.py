
import json
import pymysql
import logging
import configparser
import hashlib
import os
import shutil
import subprocess
from difflib import SequenceMatcher

class Orchestrateur():

    def __init__(self) -> None:
        self.config = self.get_config()
        logging.basicConfig(filename=f"log/orchestrateur.log",
                            format='%(asctime)s %(message)s',
                            filemode='a',
                            level=logging.INFO)
        self.logger = logging.getLogger()
        db = self.config["database"]
        connection = pymysql.connect(
            host=db["host"],
            user=db["user"],
            db=db["db"],
            password=db["pwd"],
            autocommit=1
        )
        self.cur = connection.cursor()

    def get_config(self) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config.read("configuration.conf")
        return config

    def convertResultFetchallToListOfDict(self, data, keys):
        return [
            {keys[column]: row[column] if "date" not in keys[column] else row[column].timestamp()
             for column in range(len(row))}
            for row in data
        ]

    def get_exercice(self, id_exo):
        self.cur.execute("SELECT attent, correction FROM exercice WHERE id = %s", (id_exo,))
        return self.convertResultFetchallToListOfDict(self.cur.fetchall(), ["attent", "correction"])[0]

    def get_user(self, pwd, uuid):
        self.cur.execute("SELECT id FROM user WHERE pwd = %s AND UUID = %s",
                         (hashlib.md5(pwd.encode()).hexdigest(), uuid))
        return self.cur.fetchall()[0][0]

    def lunch_correction(self, json_data, extension):
        self.logger.info(f"Début correction pour {json_data['uuidMake']} ({extension})")
        mark = 0
        upload_path = os.path.join("upload", json_data["uuidMake"])
        file_path = os.path.join(upload_path, f"{json_data['uuidMake']}.{extension}")
        output_path = os.path.join(upload_path, "result.txt")

        # Exécution sécurisée
        try:
            result = subprocess.run(
                ["python3", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                check=False
            )
            with open(output_path, "w") as f:
                f.write(result.stdout.decode())
        except subprocess.TimeoutExpired:
            self.logger.warning("Timeout du script")
            mark = 0
        except Exception as e:
            self.logger.error(f"Erreur à l'exécution : {e}")
            mark = 0

        # Comparaison avec les résultats attendus
        witness_exercice = self.get_exercice(json_data["nb_exo"])
        try:
            with open(output_path, "r") as f:
                attent_render = f.read()
        except:
            attent_render = ""

        try:
            with open(file_path, "r") as f:
                file_render = f.read()
        except:
            file_render = ""

        coeff_result = SequenceMatcher(None, witness_exercice["attent"], attent_render).ratio()
        coeff_file = SequenceMatcher(None, witness_exercice["correction"], file_render).ratio()
        mark = round(50 * coeff_result + 50 * coeff_file, 2)

        # Insertion dans la base
        try:
            user_id = self.get_user(json_data["pwd"], json_data["uuid"])
            self.cur.execute("INSERT INTO render(user, exercice, mark) VALUES (%s, %s, %s)",
                             (user_id, json_data["nb_exo"], mark))
            self.logger.info(f"Note enregistrée : {mark}")
        except Exception as e:
            self.logger.error(f"Erreur d'insertion en base : {e}")

        # Nettoyage
        try:
            shutil.rmtree(upload_path)
            self.logger.info("Fichiers supprimés.")
        except Exception as e:
            self.logger.warning(f"Erreur de suppression : {e}")

        return True

if __name__ == "__main__":
    print("Ce script est destiné à être utilisé par l'application.")
