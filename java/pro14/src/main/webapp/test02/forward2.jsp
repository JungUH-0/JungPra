<%@page import="sec01.ex01.MemberBean"%>
<%@ page language="java" contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"
    import="sec01.ex01.*"%>
<!DOCTYPE html>
<%
 	request.setCharacterEncoding("UTF-8");
	//String id = request.getParameter("id");
	//String pwd = request.getParameter("pwd");
	//String name = request.getParameter("name");
	//String email =request.getParameter("email");
	//MemberBean member=new MemberBean(id,pwd,name,email);
	//request.setAttribute("address", "서울시 강남구");
	MemberBean member=new MemberBean("lee","1234","이순신","lee@test.com");
	request.setAttribute("member", member);
%>
<html>
<head>
<meta charset="UTF-8">
<title>forward2</title>
</head>
<body>
<jsp:forward page = "member2.jsp"></jsp:forward>

</body>
</html>