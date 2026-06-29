<%@page import="sec01.ex01.MemberBean"%>
<%@ page language="java" contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"
    import="java.util.*, sec01.ex01.*"
    isELIgnored="false"%>
<!DOCTYPE html>
<%
 	request.setCharacterEncoding("UTF-8");
	List memberList=new Array();
	MemberBean m1= new MemberBean
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