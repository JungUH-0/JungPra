<%@ page language="java" contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"
    isELIgnored="false"
    import="java.util.*, sec01.ex01.*"%>
<!DOCTYPE html>
<%
 	request.setCharacterEncoding("UTF-8");
 %>
 <jsp:useBean id ="m" class="sec01.ex02.MemberBean"/> <!-- memberBean 클래스를 사용하겠다는뜻 -->
 <jsp:setProperty name="m" property="*"/> <!-- memberBean에 있는 속성들을 셋하겠다 (적용시키겠다) -->
 <jsp:useBean id="addr" class="sec01.ex02.Address"/>
 <jsp:setProperty name="addr" property="city" value="서울"/>
 <jsp:setProperty name="addr" property="zipcode" value="07654"/>
 <% 
 	m.setAddr(addr);
 	%>
 
<html>
<head>
<meta charset="UTF-8">
<title>Insert title here</title>
</head>
<body>
<table border ="1" align="center">
 	<tr align="center" bgcolor="#99ccff">
 		<td width="20%"><b>아이디</b></td>
 		<td width="20%"><b>비밀번호</b></td>
 		<td width="20%"><b>이름</b></td>
 		<td width="20%"><b>이메일</b></td>	
 		<td width="20%"><b>거주지</b></td>	
 		<td width="20%"><b>우편번호</b></td>		
 	</tr>
 	<tr align="center">
 		<td>${m.id}</td>
 		<td>${m.pwd}</td>
 		<td>${m.name}</td>
 		<td>${m.email}</td>
 		<td><%=m.getAddr().getCity()%> </td>
 		<td><%=m.getAddr().getZipcode()%> </td>
 	</tr>
 
 	<tr align="center">
 		<td>${m.id}</td>
 		<td>${m.pwd}</td>
 		<td>${m.name}</td>
 		<td>${m.email}</td>
 		<td>${m.addr.city}</td>
 		<td>${m.addr.zipcode}</td>
 	</tr>
 	
</table>

</body>
</html>