/**
 * @author Natan Ogliari
 * @version 0.1
 */


package classes;

import java.awt.EventQueue;

import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.border.EmptyBorder;
import javax.swing.JLabel;
import javax.swing.JOptionPane;

import java.awt.Font;
import java.awt.Color;
import javax.swing.JTextField;
import javax.swing.UIManager;
import javax.swing.JPasswordField;
import javax.swing.JButton;
import java.awt.event.ActionListener;
import java.sql.Connection;
import java.sql.SQLException;
import java.awt.event.ActionEvent;
import java.sql.PreparedStatement;
import java.sql.ResultSet;

public class tela_de_acesso extends JFrame {

	private JPanel contentPane;
	private JTextField tfUsuario;
	private JPasswordField pfSenha;

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					tela_de_acesso frame = new tela_de_acesso();
					frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}

	/**
	 * Create the frame.
	 */
	public tela_de_acesso() {
		setResizable(false);
		setTitle("Início\r\n");
		setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		setBounds(100, 100, 292, 250);
		contentPane = new JPanel();
		contentPane.setBorder(new EmptyBorder(5, 5, 5, 5));

		setContentPane(contentPane);
		contentPane.setLayout(null);
		
		JLabel lblNewLabel = new JLabel("Usuário:");
		lblNewLabel.setBackground(new Color(240, 240, 240));
		lblNewLabel.setFont(new Font("Arial", Font.PLAIN, 16));
		lblNewLabel.setBounds(28, 50, 74, 19);
		contentPane.add(lblNewLabel);
		
		tfUsuario = new JTextField();
		tfUsuario.setFont(new Font("Arial", Font.PLAIN, 16));
		tfUsuario.setBounds(89, 51, 152, 18);
		contentPane.add(tfUsuario);
		tfUsuario.setColumns(10);
		
		JLabel lblSenha = new JLabel("Senha:");
		lblSenha.setFont(new Font("Arial", Font.PLAIN, 16));
		lblSenha.setBackground(UIManager.getColor("Button.background"));
		lblSenha.setBounds(28, 80, 74, 19);
		contentPane.add(lblSenha);
		
		pfSenha = new JPasswordField();
		pfSenha.setFont(new Font("Arial", Font.PLAIN, 16));
		pfSenha.setBounds(89, 80, 152, 19);
		contentPane.add(pfSenha);
		
		JButton btnEntrar = new JButton("Entrar");
		btnEntrar.addActionListener(new ActionListener() {
			
			  /**
		     * Realiza a confirmação de acesso do banco de dados sql
		     * 
		     */	
			
			public void actionPerformed(ActionEvent e) {
				
				try {
					Connection con = conexao.faz_conexao();
					
					String sql = "select * from db_pautapr29.pauta where usuario=? and senha=?"; 
					PreparedStatement stmt = (PreparedStatement) con.prepareStatement(sql);
					 stmt.setString(1, tfUsuario.getText());
					 stmt.setString(2,  new String(pfSenha.getPassword()));
					 
					 ResultSet rs = stmt.executeQuery();
					 
					 if(rs.next()) {
						 
						 Tela_cadastro exibir = new Tela_cadastro();
						 exibir.setVisible(true);
						 
						 setVisible(false);
						 						 
					 }else {
						 JOptionPane.showMessageDialog(null, "Esse usuário não existe");
					 }
					stmt.close();
					con.close();
					
				} catch (SQLException e1) {
					e1.printStackTrace();
				}
				
				
			}
		});
		btnEntrar.setFont(new Font("Arial Black", Font.PLAIN, 18));
		btnEntrar.setBounds(89, 127, 152, 49);
		contentPane.add(btnEntrar);
	}
}
