<%@ page contentType="text/html;charset=ISO-8859-1" %>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<html>
<body>
<h1>Claim ${claim.claimNumber}</h1>
<ul class="tabs">
  <li><a href="#summary">Summary</a></li>
  <li><a href="#notes">Notes</a></li>
  <li><a href="#reserves">Reserves</a></li>
<% if (request.isUserInRole("AUDITOR")) { %>
  <li><a href="#audit">Audit trail</a></li>
<% } %>
</ul>
<c:forEach var="n" items="${claim.notes}">
  <p>${n.text}</p>
</c:forEach>
</body>
</html>
