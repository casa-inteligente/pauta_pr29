/**
 * @author Natan Ogliari
 * @version 0.1
 */


package classes;

import java.sql.*;


public class conexao {
	
	private static String caminho = "jdbc:mysql://localhost/db_pautapr29";
	private static String usuario = "root";
	private static String senha = "5300";
	
	
	  /**
     * Realiza a conexção ao banco de dados
     * @return retorna a  conexão do banco de dados
     */
	
	public static Connection faz_conexao() throws SQLException {
				
		try {
		Class.forName("com.mysql.jdbc.Driver");
		
		return DriverManager.getConnection(caminho, usuario, senha);		
			
		}catch (ClassNotFoundException e) {
			throw new SQLException(e.getException());
			
		}
				
	}

}
