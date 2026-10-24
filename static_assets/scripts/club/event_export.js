(() => {
	u(".date-utc").each((el) => {
		$el = u(el);
		$el.text(dayjs($el.data("date")).local().format("YYYY-MM-DD HH:mm:ss"));
	});
	u("#two-d-rerun-export-form").on("submit", (e) => {
		e.preventDefault();
		const formData = new FormData(e.target);

		let rerunArgs = `${formData.get("event_id")}/${formData.get("map_idx")}`;
		if (formData.get("tag")) {
			rerunArgs += `/${formData.get("tag")}`;
		}
		window.open(
			`http://3drerun.worldofo.com/2d/?server=${encodeURIComponent(formData.get("api_root"))}woo&eventid=${encodeURIComponent(rerunArgs)}&liveid=-`,
		);
	});

	u("#mapdump-export-form").on("submit", (e) => {
		e.preventDefault();
		const formData = new FormData(e.target);

		const params = {
			title: formData.get("title"),
			kmz:
				"https:" +
				formData.get("api_root") +
				"events/" +
				formData.get("event_id") +
				"/maps/" +
				formData.get("map_idx") +
				".kmz",
			gpx:
				"https:" +
				formData.get("api_root") +
				"competitors/" +
				formData.get("runner") +
				"/gpx",
		};
		const queryString = new URLSearchParams(params).toString();
		window.open(`https://mapdump.com/new#` + queryString);
	});

	u("#gpx-export-form").on("submit", (e) => {
		e.preventDefault();
		const formData = new FormData(e.target);
		window.open(
			"https:" +
				formData.get("api_root") +
				"competitors/" +
				formData.get("runner") +
				"/gpx",
		);
	});

	u("#map-export-form").on("submit", (e) => {
		e.preventDefault();
		const formData = new FormData(e.target);
		if (e.submitter.name === "map-kmz") {
			window.open(
				"https:" +
					formData.get("api_root") +
					"events/" +
					formData.get("event_id") +
					"/maps/" +
					formData.get("map_idx") +
					".kmz",
			);
		} else {
			window.open(
				"https:" +
					formData.get("api_root") +
					"events/" +
					formData.get("event_id") +
					"/maps/" +
					formData.get("map_idx") +
					".jpeg",
			);
		}
	});
})();
