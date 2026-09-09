from datetime import datetime

import psycopg2

from Excepcion import Excepcion


class MemeRepositorio():
    __conexion = None

    def __init__(self, conexion):
        self.__conexion = conexion

    def existe_meme(self, nombre: str, url: str):
        try:
            cur = self.__conexion.cursor()

            with self.__conexion.cursor() as cur:
                cur.execute("""SELECT COUNT(*)
                            FROM memes
                            WHERE nombre_imagen = %s AND url = %s;""", (nombre, url))
                
                cuenta: int = cur.fetchone()[0]
        except psycopg2.Error as e:
            raise Excepcion(f"Error al comprobar si existe el meme {nombre} y url {url}: {e.pgcode} - {e.pgerror}") from e

        if cuenta > 0:
            return True

        return False

    def guardar_meme(self, nombre: str, url: str, resp_analisis: str):
        try:
            with self.__conexion.cursor() as cur:
                cur.execute("""INSERT INTO memes (nombre_imagen, url, fecha_insercion, resp_analisis)
                               VALUES (%s, %s, %s, %s);""", (nombre, url, datetime.now(), resp_analisis))
                
                self.__conexion.commit()
        except psycopg2.Error as e:
            raise Excepcion(f"Error al guardar el meme {nombre} y url {url}: {e.pgcode} - {e.pgerror}") from e
