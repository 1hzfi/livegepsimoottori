function onGPXLoaded(e) {
	const xml = e.target.result;
	let parsedGpx;
	try {
		parsedGpx = parseGpx(xml);
	} catch (e) {
		return [{}, "Invalid GPX file"];
	}
	const newRoute = [];
	if (parsedGpx.segments.length === 0) {
		return [{}, "No locations found in this file"];
	}
	let missingTimeInfo = false;
	for (const segment of parsedGpx.segments) {
		for (const pos of segment) {
			if (pos.loc[0]) {
				if (pos.time) {
					newRoute.push({ time: pos.time, latLon: [pos.loc[0], pos.loc[1]] });
				} else {
					missingTimeInfo = true;
				}
			}
		}
	}
	return onRouteLoaded(newRoute, missingTimeInfo);
}

const onTCXLoaded = (e) => {
	const xml = e.target.result;
	try {
		let route;
		parseTCXString(xml, (wo) => {
			route = onTCXParsed(wo);
		});
		return [route, null];
	} catch (e) {
		return [{}, "Invalid TCX file"];
	}
};

const onFitLoaded = (e) => {
	var fitParser = new Fit.FitParser({
		force: true,
		speedUnit: "km/h",
		lengthUnit: "km",
		temperatureUnit: "celsius",
		elapsedRecordField: "timer_time",
		mode: "list",
	});
	let route = {};
	let error = null;
	fitParser.parse(e.target.result, (err, data) => {
		if (err) {
			error = "Invalid FIT file";
			return;
		}
		const newRoute = [];
		let missingTimeInfo = false;
		for (const rec of data.records) {
			if (rec.position_lat) {
				if (rec.timestamp) {
					newRoute.push({
						time: +rec.timestamp,
						latLon: [rec.position_lat, rec.position_long],
					});
				} else {
					missingTimeInfo = true;
				}
			}
		}
		[route, error] = onRouteLoaded(newRoute, missingTimeInfo);
	});
	return [route, error];
};

function onRouteLoaded(newRoute, missingTimeInfo) {
	if (!newRoute?.length) {
		if (missingTimeInfo) {
			return [{}, "No points with time information found in this file"];
		}
		return [{}, "No locations found in this file"];
	}
	const ts = newRoute.map((pt) => Math.round(+pt.time / 1e3)).join(",");
	const latlngs = newRoute
		.map((pt) => `${+pt.latLon[0].toFixed(5)} ${+pt.latLon[1].toFixed(5)}`)
		.join(",");
	const route = { timestamps: ts, latlngs: latlngs };
	if (JSON.stringify(route).length > 2 * 1e7) {
		return [{}, "File is too big"];
	}
	return [route, null];
}

function getGpxData(node, resultRaw) {
	const result = resultRaw ?? { segments: [] };
	switch (node.nodeName) {
		case "name":
			result.name = node.textContent;
			break;
		case "trkseg": {
			const segment = [];
			result.segments.push(segment);
			for (let i = 0; i < node.childNodes.length; i++) {
				const snode = node.childNodes[i];
				if (snode.nodeName === "trkpt") {
					const trkpt = {
						loc: [
							Number.parseFloat(snode.attributes.lat.value),
							Number.parseFloat(snode.attributes.lon.value),
						],
					};
					for (let j = 0; j < snode.childNodes.length; j++) {
						const ssnode = snode.childNodes[j];
						if (ssnode.nodeName === "time") {
							trkpt.time = new Date(ssnode.childNodes[0].data);
						}
					}
					segment.push(trkpt);
				}
			}
			break;
		}
		case "rte": {
			const segment = [];
			result.segments.push(segment);
			for (let i = 0; i < node.childNodes.length; i++) {
				const snode = node.childNodes[i];
				if (snode.nodeName === "rtept") {
					const rtept = {
						loc: [
							Number.parseFloat(snode.attributes.lat.value),
							Number.parseFloat(snode.attributes.lon.value),
						],
					};
					for (let j = 0; j < snode.childNodes.length; j++) {
						const ssnode = snode.childNodes[j];
						if (ssnode.nodeName === "time") {
							rtept.time = new Date(ssnode.childNodes[0].data);
						}
					}
					segment.push(rtept);
				}
			}
			break;
		}
		case "wpt": {
			const wpt = {
				loc: [
					Number.parseFloat(node.attributes.lat.value),
					Number.parseFloat(node.attributes.lon.value),
				],
			};
			for (let j = 0; j < node.childNodes.length; j++) {
				const ssnode = node.childNodes[j];
				if (ssnode.nodeName === "time") {
					wpt.time = new Date(ssnode.childNodes[0].data);
				}
			}
			result.segments.push([wpt]);
			break;
		}
		default:
			break;
	}
	for (let i = 0; i < node.childNodes.length; i++) {
		getGpxData(node.childNodes[i], result);
	}
	return result;
}

const onTCXParsed = (workout) => {
	const newRoute = [];
	let missingTimeInfo = false;
	for (const lap of workout.laps) {
		for (const pos of lap.track) {
			if (pos.latitude) {
				if (pos.datetime) {
					newRoute.push({
						time: +pos.datetime,
						latLon: [pos.latitude, pos.longitude],
					});
				} else {
					missingTimeInfo = true;
				}
			}
		}
	}
	return onRouteLoaded(newRoute, missingTimeInfo);
};

function parseGpx(xmlstr) {
	if (typeof DOMParser === "undefined") {
		function DOMParser() {}
		DOMParser.prototype.parseFromString = (
			str,
			contentType = "application/xml",
		) => {
			if (typeof XMLHttpRequest !== "undefined") {
				const xmldata = new XMLHttpRequest();
				xmldata.open(
					"GET",
					`data:${contentType};charset=utf-8,${encodeURIComponent(str)}`,
					false,
				);
				if (xmldata.overrideMimeType) {
					xmldata.overrideMimeType(contentType);
				}
				xmldata.send(null);
				return xmldata.responseXML;
			}
		};
	}
	const doc = new DOMParser().parseFromString(xmlstr, "text/xml");
	return getGpxData(doc.documentElement);
}

function selectizeDeviceInput(field) {
	return new TomSelect(field, {
		valueField: "device_id",
		labelField: "device_id",
		searchField: "device_id",
		create: false,
		createOnBlur: false,
		persist: false,
		plugins: ["preserve_on_blur"],
		load: (query, callback) => {
			if (query.length < 4) {
				return callback();
			}
			reqwest({
				url: `${window.local.apiBaseUrl}search/device?q=${encodeURIComponent(query)}`,
				method: "get",
				type: "json",
				withCredentials: true,
				crossOrigin: true,
				success: (res) => {
					callback(res.results);
				},
				error: () => {
					callback();
				},
			});
		},
	});
}

renderGPSUploader = (el, onValidCB, onErrorCB) => {
	const gpsUploader = u(el);
	if (gpsUploader.nodes.length) {
		const gpsFileInput = gpsUploader.closest("input[type=file]");
		gpsFileInput.attr("accept", ".gpx,.tcx,.fit");
		gpsFileInput.on("change", function () {
			gpsFileInput.removeClass("was-validated", "is-valid", "is-invalid");
			gpsFileInput.closest(".invalid-feedback").remove();

			if (this.files.length > 0) {
				gpsFileInput.parent().find(".invalid-feedback").remove();
				const gpsFile = this.files[0];
				const filename = gpsFile.name;
				const fr = new FileReader();
				let onload = null;
				let readFunction = "readAsText";
				if (filename.toLowerCase().endsWith(".tcx")) {
					onload = onTCXLoaded;
				} else if (filename.toLowerCase().endsWith(".fit")) {
					onload = onFitLoaded;
					readFunction = "readAsArrayBuffer";
				} else {
					onload = onGPXLoaded;
				}

				fr.onload = (e) => {
					const [route, error] = onload(e);
					console.log("route", route, "error", error);
					const jsonBlob = new Blob([JSON.stringify(route)], {
						type: "text/plain;charset=us-ascii",
					});
					const jsonFile = new File([jsonBlob], filename, {
						type: "text/plain",
					});
					const dataTransfer = new DataTransfer();
					dataTransfer.items.add(jsonFile);
					const inputElement = gpsFileInput.nodes[0];
					inputElement.files = dataTransfer.files;
					if (error) {
						gpsFileInput
							.addClass("was-validated", "is-invalid")
							.removeClass("is-valid")
							.after(
								'<div class="invalid-feedback">Invalid GPS file (' +
									error +
									")</div>",
							);
						if (onErrorCB) onErrorCB();
						return;
					}
					gpsFileInput
						.addClass("was-validated", "is-valid")
						.removeClass("is-invalid")
						.after('<div class="valid-feedback">File ready for upload</div>');
					if (onValidCB) onValidCB();
				};

				fr[readFunction](gpsFile);
			}
		});
		gpsFileInput.trigger("change");
	}
};

(() => {
	if (u("#registration-form").nodes.length) {
		u("#id_race_complete").on("change", (e) => {
			e.preventDefault();
			const input = u("#id_gps_file");
			if (u("#id_gps_file").attr("type") !== "hidden")
				if (u("#id_race_complete").nodes[0].checked) {
					input.parent().removeClass("d-none");
				} else {
					u("#id_gps_file").parent().addClass("d-none");
					u("#id_gps_file").val(null);
					signUpRoute = null;
				}
		});
		u("#id_race_complete").trigger("change");
		renderGPSUploader("#id_gps_file", () => {
			const selectEl = document.getElementById("id_device");
			const control = selectEl?.tomselect;
			control?.clear();
		});
	}
	// Selectize Device selector
	if (u("#registration-form").nodes.length) {
		const tsDevId = selectizeDeviceInput("select[name='device']");
		const warningHTML = u("<div>")
			.append(u("#warning-if-device-id").html())
			.addClass("d-none");
		u("#id_device_helptext").append(warningHTML);
		u("select[name='device']").on("change", (e) => {
			if (e.target.value) {
				signUpRoute = null;
				u("#id_gps_file").val(null);
				warningHTML.removeClass("d-none");
			} else {
				warningHTML.addClass("d-none");
			}
		});
		let deviceIdfromHash = false;
		if (window.location.hash) {
			const hash = window.location.hash;
			window.history.pushState("-", null, window.location.pathname);
			const searchParams = new URLSearchParams(hash.slice(1));
			const deviceId = searchParams.get("device_id");
			if (deviceId) {
				deviceIdfromHash = true;
				tsDevId.clear();
				tsDevId.clearOptions();
				tsDevId.addOption({ device_id: deviceId });
				tsDevId.setValue(deviceId);
			}
		}
		const savedRegistrationInfoRaw = window.localStorage.getItem(
			"userInfoRegistration",
		);
		if (savedRegistrationInfoRaw) {
			const savedRegistrationInfo = JSON.parse(savedRegistrationInfoRaw);
			const { name, shortName, deviceId } = savedRegistrationInfo;
			u("#id_name").val(name);
			u("#id_short_name").val(shortName);
			if (deviceId && !deviceIdfromHash) {
				tsDevId.clear();
				tsDevId.clearOptions();
				tsDevId.addOption({ device_id: deviceId });
				tsDevId.setValue(deviceId);
				deviceIdfromHash = true;
			}
		}
	}

	renderGPSUploader("#id_gpx_file");
	u(".date-utc").each((el) => {
		$el = u(el);
		$el.text(dayjs($el.data("date")).local().format("LLLL"));
	});
})();
