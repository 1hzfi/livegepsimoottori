document.getElementById("djhj-hide-btn")?.addEventListener("click", (e) => {
	e.preventDefault();
	document.getElementById("djhj").style.display = "none";
});
if (window.location.host.split(".")[0] !== "dashboard") {
	document.getElementById("djhj-release-btn").remove();
}
