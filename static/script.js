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
var lightboxImages = [];
var lightboxIndex = 0;

function updateLightboxImage() {
	var imageNode = document.getElementById("lbImage");
	var counterNode = document.getElementById("lbCounter");
	var toolbarNode = document.getElementById("lbToolbar");

	if (!imageNode) {
		return;
	}

	if (lightboxImages.length > 0) {
		imageNode.src = lightboxImages[lightboxIndex];
		imageNode.style.display = "block";
		if (counterNode) {
			counterNode.textContent = (lightboxIndex + 1) + " / " + lightboxImages.length;
		}
		if (toolbarNode) {
			toolbarNode.style.display = lightboxImages.length > 1 ? "flex" : "none";
		}
	} else {
		imageNode.removeAttribute("src");
		imageNode.style.display = "none";
		if (toolbarNode) {
			toolbarNode.style.display = "none";
		}
	}
}

function openLightbox(el) {
	var title = el.getAttribute("data-title") || el.querySelector("h3") && el.querySelector("h3").innerText || "";
	var desc = el.getAttribute("data-desc") || el.querySelector("p") && el.querySelector("p").innerText || "";
	var image = el.getAttribute("data-image") || "";
	var imagesData = el.getAttribute("data-images") || "";

	lightboxImages = [];
	lightboxIndex = 0;

	if (imagesData) {
		lightboxImages = imagesData.split("|").map(function (item) {
			return item.trim();
		}).filter(Boolean);
	} else if (image) {
		lightboxImages = [image];
	}

	updateLightboxImage();

	document.getElementById("lbTitle").innerHTML = title;
	document.getElementById("lbBody").innerHTML = desc;
	document.getElementById("lbOverlay").classList.add("open");
	document.body.style.overflow = "hidden";
}

function showPrevImage(e) {
	if (e) {
		e.stopPropagation();
	}
	if (lightboxImages.length <= 1) {
		return;
	}
	lightboxIndex = (lightboxIndex - 1 + lightboxImages.length) % lightboxImages.length;
	updateLightboxImage();
}

function showNextImage(e) {
	if (e) {
		e.stopPropagation();
	}
	if (lightboxImages.length <= 1) {
		return;
	}
	lightboxIndex = (lightboxIndex + 1) % lightboxImages.length;
	updateLightboxImage();
}

function closeLightbox(e) {
	if (!e || e.target === document.getElementById("lbOverlay") || e.currentTarget.classList.contains("lb-close")) {
		document.getElementById("lbOverlay").classList.remove("open");
		var imageNode = document.getElementById("lbImage");
		if (imageNode) {
			imageNode.removeAttribute("src");
		}
		lightboxImages = [];
		lightboxIndex = 0;
		document.body.style.overflow = "";
	}
}

document.addEventListener("keydown", function (e) {
	if (e.key === "Escape") {
		var overlay = document.getElementById("lbOverlay");
		if (overlay && overlay.classList.contains("open")) {
			overlay.classList.remove("open");
			var imageNode = document.getElementById("lbImage");
			if (imageNode) {
				imageNode.removeAttribute("src");
			}
			lightboxImages = [];
			lightboxIndex = 0;
			document.body.style.overflow = "";
		}
	} else if (e.key === "ArrowLeft") {
		showPrevImage();
	} else if (e.key === "ArrowRight") {
		showNextImage();
	}
});
