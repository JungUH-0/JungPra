<%@ page language="java" contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"
    isELIgnored="false"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<% request.setCharacterEncoding("UTF-8");%>

	<c:set var="id" value="hong" scope="page" />
	<c:set var="pwd" value="1234" scope="page" />
	<%-- <c:set var="name" value="${'홍길동'}" scope="page" />--%>
	<c:set var="age" value="${22}" scope="page" />
	<c:set var="height" value="${177}" scope="page" />
	 
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>회원 정보 출력창</title>
</head>
<body>
    
    <table border=1  align="center"  >
        <tr align="center" bgcolor="lightgreen">
            <td width="20%"><b>아이디</b></td>
            <td width="20%"><b>비밀번호</b></td>
            <td width="20%"><b>이름</b></td>
            <td width="20%"><b>나이</b></td>
            <td width="20%"><b>키</b></td>
        </tr>
        <c:choose>
        	<c:when test="${empty name}">
	    <tr align="center">
	        <td colspan=5 >이름을 입력하세요!!</td>
	    </tr>
			</c:when>
			<c:otherwise >
	    <tr align="center">
	        <td>${id}</td>
	        <td>${pwd}</td>
	        <td>${name}</td>
	        <td>${age}</td>
	        <td>${height}</td>
	    </tr>
</c:otherwise>
</c:choose>
        </table>
    <!-- 
  <c:if test="${true}">
    <h1>항상 참입니다.</h1>
</c:if>

<c:if test="${11==11}">
    <h1>두 값은 같습니다.</h1>
</c:if>

<c:if test="${11!=31}">
    <h1>두 값은 같지 않습니다.</h1>
</c:if>

<c:if test="${(id=='hong') && (name=='홍길동')}">
    <h1>아이디는 ${id}이고, 이름은 ${name}입니다.</h1>
</c:if>

<c:if test="${age==22}">
    <h1>${name}의 나이는 ${age}살입니다.</h1>
</c:if>

<c:if test="${height>160}">
    <h1>${name}의 키는 160보다 큽니다.</h1>
</c:if>
     -->
</body>
</html>