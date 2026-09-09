import psycopg2

from Excepcion import Excepcion

class BD:
    _conexion = None

    @classmethod
    def abrir_conexion(self, host, port, dbName, user, password):
        if self._conexion is None:
            try:
                self._conexion = psycopg2.connect(host=host,
                                                  port=port,
                                                  dbname=dbName,
                                                  user=user,
                                                  password=password)
            except psycopg2.Error as e:
                raise Excepcion(f"Error al abrir la conexión: {e.pgcode} - {e.pgerror}") from e

        return self._conexion

    @classmethod
    def cerrar_conexion(self):
        if self._conexion is not None:
            try:
                self._conexion.close()
            except psycopg2.Error as e:
                raise Excepcion(f"Error al cerrar la conexión: {e.pgcode} - {e.pgerror}") from e
