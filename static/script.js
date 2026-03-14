document.addEventListener("DOMContentLoaded", function () {
	const revealItems = document.querySelectorAll(".reveal-up");
	const navbar = document.querySelector(".academy-navbar");

	if ("IntersectionObserver" in window) {
		const observer = new IntersectionObserver(
			function (entries) {
				entries.forEach(function (entry) {
					if (entry.isIntersecting) {
						entry.target.classList.add("is-visible");
						observer.unobserve(entry.target);
					}
				});
			},
			{ threshold: 0.15 }
		);

		revealItems.forEach(function (item) {
			observer.observe(item);
		});
	} else {
		revealItems.forEach(function (item) {
			item.classList.add("is-visible");
		});
	}

	function updateNavbarState() {
		if (!navbar) {
			return;
		}

		if (window.scrollY > 20) {
			navbar.classList.add("is-scrolled");
		} else {
			navbar.classList.remove("is-scrolled");
		}
	}

	updateNavbarState();
	window.addEventListener("scroll", updateNavbarState, { passive: true });
});

/* ── Gallery Lightbox ── */
function openLightbox(el) {
	var title = el.getAttribute("data-title") || el.querySelector("h3") && el.querySelector("h3").innerText || "";
	var desc = el.getAttribute("data-desc") || el.querySelector("p") && el.querySelector("p").innerText || "";
	document.getElementById("lbTitle").innerHTML = title;
	document.getElementById("lbBody").innerHTML = desc;
	document.getElementById("lbOverlay").classList.add("open");
	document.body.style.overflow = "hidden";
}

function closeLightbox(e) {
	if (!e || e.target === document.getElementById("lbOverlay") || e.currentTarget.classList.contains("lb-close")) {
		document.getElementById("lbOverlay").classList.remove("open");
		document.body.style.overflow = "";
	}
}

document.addEventListener("keydown", function (e) {
	if (e.key === "Escape") {
		var overlay = document.getElementById("lbOverlay");
		if (overlay && overlay.classList.contains("open")) {
			overlay.classList.remove("open");
			document.body.style.overflow = "";
		}
	}
});
