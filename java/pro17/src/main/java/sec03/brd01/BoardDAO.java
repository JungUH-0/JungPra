package sec03.brd01;

import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.ArrayList;
import java.util.List;

import javax.naming.Context;
import javax.naming.InitialContext;
import javax.sql.DataSource;

public class BoardDAO {
	private DataSource dataFactory;
	Connection conn;
	PreparedStatement pstmt;
	
	public BoardDAO() {
		try {
			Context ctx = new InitialContext();
			Context envContext = (Context) ctx.lookup("java:/comp/env");
			dataFactory = (DataSource)envContext.lookup("jdbc/oracle");
			
		}catch (Exception e) {
			// TODO: handle exception
			e.printStackTrace();
		}	
	}
	public List selectAllArticles() {
		List articlesList = new ArrayList();
		try {
			conn = dataFactory.getConnection();
			String query = "select level, articleno, parentno, title, content, id, writeDate "			
					+"from t_board "
					+"start with parentno=0 "
					+"connect by prior articleno = parentno "
					+"order SIBLINGS by articleno desc";
			
			System.out.println("query :"+query);
			pstmt = conn.prepareStatement(query);
			ResultSet rs = pstmt.executeQuery();
			
			while (rs.next()) {
				int level = rs.getInt("level");
				int articleNo = rs.getInt("articleno");
				int parentNo = rs.getInt("parentno");
				String title = rs.getString("title");
				String content = rs.getString("content");
				String id =rs.getString("id");
				Date writeDate = rs.getDate("writeDate");
				
				ArticleVO article = new ArticleVO();
				article.setLevel(level);
				article.setArticleNO(articleNo);
				article.setParentNO(parentNo);
				article.setTitle(title);
				article.setContent(content);
				article.setId(id);
				article.setWriteDate(writeDate);
				articlesList.add(article);
				
			}
			rs.close();
			pstmt.close();
			conn.close();
		}catch (Exception e) {
			// TODO: handle exception
		}
		return articlesList;
	}
}
