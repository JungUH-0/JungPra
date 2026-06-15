package sec01.ex02;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

//public class MemberDAO {
//	private Connection con;
//	private PreparedStatement pstmt;
//	private DataSource dataFactory;
//	
//	private static final String driver = "oracle.jdbc.driver.OracleDriver";
//	private static final String url = "jdbc:oracle:thin:@localhost:1521:testdb";
//	private static final String user = "scott";
//	private static final String pwd = "tiger";
//	
//	public List listMembers() {
//		List list =new ArrayList();
//		try
//		{
//			connDB();
////			String query = "select *from t_member";
////			System.out.println(query);
////			ResultSet rs = stmt.executeQuery(query);
//			con =dataFactory.getConnection();
//			String query = "select *from t_member";
//			System.out.println("prepareStatment"+query);
//			pstmt = con.prepareStatement(query);
//			ResultSet rs = pstmt.executeQuery(query);
//			
//			while(rs.next()) {
//				String id = rs.getString("id");
//				String pwd = rs.getString("pwd");
//				String name = rs.getString("name");
//				String email = rs.getString("email");
//				Date joinDate = rs.getDate("joinDate");
//				MemberVO vo = new MemberVO();
//				vo.setId(id);
//				vo.setPwd(pwd);
//				vo.setName(name);
//				vo.setEmail(email);
//				vo.setJoinDate(joinDate);
//				list.add(vo);
//				
//			}
//			rs.close();
//			pstmt.close();
//			con.close();
//			
//		}catch (Exception e) {
//			// TODO: handle exception
//			e.printStackTrace();
//		}
//		return list;
//	}
//	private void connDB() {
//		try {
//			Class.forName(driver);
//			System.out.println("oracle 드라이버 로딩 성공");
//			con = DriverManager.getConnection(url,user,pwd);
//			System.out.println("Connection 생성 성공");
//			pstmt = (PreparedStatement) con.createStatement();
//			System.out.println("Statement 생성 성공");	
//
//			}catch (Exception e) {
//			// TODO: handle exception
//			e.printStackTrace();
//		}
//	}
//}
public class MemberDAO {
	private Connection con;
	private PreparedStatement pstmt;
	
	private static final String driver = "oracle.jdbc.driver.OracleDriver";
    private static final String url = "jdbc:oracle:thin:@localhost:1521:testdb";
    private static final String user = "scott";
    private static final String pwd = "tiger";
	public List listMembers() {
		List list = new ArrayList();
		try {
			connDB();
			String query = "select * from t_member";
			System.out.println("PreparedStatement : " + query);
			pstmt = con.prepareStatement(query);
			ResultSet rs = pstmt.executeQuery(query);
			while(rs.next()) {
				String id = rs.getString("id");
				String pwd = rs.getString("pwd");
				String name = rs.getString("name");
				String email = rs.getString("email");
				Date joinDate = rs.getDate("joinDate");
				MemberVO vo = new MemberVO();
				vo.setId(id);
				vo.setPwd(pwd);
				vo.setName(name);
				vo.setEmail(email);
				vo.setJoinDate(joinDate);
				list.add(vo);
			}
			rs.close();
			pstmt.close();
			con.close();
		} catch (Exception e)
		{
			e.printStackTrace();
		}
		return list;
	}
	private void connDB() {
		try {
			Class.forName(driver);
			System.out.println("Oracle 드라이버 로딩 성공");
			con = DriverManager.getConnection(url, user, pwd);
			System.out.println("Connection 생성 성공");
		} catch(Exception e) {
			e.printStackTrace();
		}
	}
}
