<%!
     from pdoc.html_helpers import minify_css
%>

<%def name="homelink()" filter="minify_css">
.homelink {
  display: block;
  color: #111827;
  font-family: "Poppins", sans-serif;
  font-size: 2em;
  font-weight: 500;
  padding-bottom: 0.5em;
}
.homelink:hover {
  color: #2d7334;
}
.homelink img {
  max-width: 30%;
  max-height: 5em;
  margin: auto;
  margin-bottom: 0.3em;
}
</%def>


<%def name="override()" filter="minify_css">
a {
  color: #2d7334;
}
a:hover {
  color: #34b458;
}

.ident {
  color: #34b458;
  font-weight: 600;
  font-family: "Poppins", sans-serif;
}

.name {
  background: #effaf1;
}
dt:target .name {
  background: #e7f8c9;
}
</%def>


<style>${override()}</style>
<style>${homelink()}</style>

<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;600&display=swap" rel="stylesheet" />
