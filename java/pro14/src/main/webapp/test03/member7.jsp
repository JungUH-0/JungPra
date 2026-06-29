<%@ page language="java" contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"
    isELIgnored="false"
    import="java.util.*,sec01.ex01.*"%>
    <%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<!DOCTYPE html>
<%
	request.setCharacterEncoding("UTF-8");
	List membersList = new ArrayList();
	MemberBean m1 = new MemberBean("son","1234","손흥민","son@text.com");
	MemberBean m2 = new MemberBean("ki","4321","기성용","ki@text.com");
	MemberBean m3 = new MemberBean("park","1212","박지성","park@text.com");
	membersList.add(m1);
	membersList.add(m2);
	membersList.add(m3);
%>
<c:set var="membersList" value="<%=membersList %>"/>
<html>
<head>
<meta charset="UTF-8">
<title>출력창</title>
</head>
<body>
	 <table border=1  align="center"  >
        <tr align="center" bgcolor="lightgreen">
            <td width="20%"><b>아이디</b></td>
            <td width="20%"><b>비밀번호</b></td>
            <td width="20%"><b>이름</b></td>
            <td width="20%"><b>이메일</b></td>
        </tr>
        <c:forEach var="i" begin="0" end="2" step="1">
     	<tr align="center">
     		<td>${membersList[i].id}</td>
     		<td>${membersList[i].pwd}</td>
     		<td>${membersList[i].name}</td>
     		<td>${membersList[i].email}</td>
     	</tr>
     	</c:forEach>
     </table>

</body>
</html>