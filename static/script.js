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

	// ── Sticky Navbar ──
	function updateNavbarState() {
		if (!navbar) {
			return;
		}

		if (window.scrollY > 20) {
			navbar.classList.add("navbar-scrolled");
		} else {
			navbar.classList.remove("navbar-scrolled");
		}
	}

	updateNavbarState();
	window.addEventListener("scroll", updateNavbarState, { passive: true });

	// ── Testimonials Carousel ──
	const testimonialDots = document.querySelectorAll(".carousel-dot");
	const testimonialCard = document.querySelector(".testimonial-card");
	
	const testimonials = [
		{
			stars: "★★★★★",
			text: "Subhash Academy gave me the perfect foundation for my IT career. The faculty support and practical labs made all the difference.",
			avatar: "RD",
			name: "Rajesh Dutt",
			role: "BCA Graduate, Google"
		},
		{
			stars: "★★★★★",
			text: "The practical exposure and mentoring at Subhash Academy helped me land my dream job. Highly recommend for anyone serious about IT.",
			avatar: "AK",
			name: "Ananya Kumar",
			role: "PGDCA Graduate, Microsoft"
		},
		{
			stars: "★★★★★",
			text: "Great institution with excellent faculty and infrastructure. The projects I worked on here became part of my portfolio that impressed employers.",
			avatar: "MS",
			name: "Mohit Singh",
			role: "BCA Graduate, HCL Tech"
		}
	];

	let currentTestimonial = 0;

	function updateTestimonial(index) {
		if (!testimonialCard) return;
		
		const testimonial = testimonials[index];
		testimonialCard.innerHTML = `
			<div class="testimonial-stars">${testimonial.stars}</div>
			<p class="testimonial-text">"${testimonial.text}"</p>
			<div class="testimonial-author">
				<div class="testimonial-avatar">${testimonial.avatar}</div>
				<div class="testimonial-meta">
					<h4>${testimonial.name}</h4>
					<p>${testimonial.role}</p>
				</div>
			</div>
		`;
		
		testimonialDots.forEach((dot, i) => {
			if (i === index) {
				dot.classList.add("active");
			} else {
				dot.classList.remove("active");
			}
		});
	}

	// Add click handlers to carousel dots
	testimonialDots.forEach((dot, index) => {
		dot.addEventListener("click", function () {
			currentTestimonial = index;
			updateTestimonial(index);
		});
	});

	// Auto-rotate testimonials every 6 seconds
	setInterval(function () {
		currentTestimonial = (currentTestimonial + 1) % testimonials.length;
		updateTestimonial(currentTestimonial);
	}, 6000);
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

/* ========== MODERN HOMEPAGE ANIMATIONS ========== */

// Counter Animation for Statistics
function animateCounter(element, target) {
	if (!target || isNaN(target)) {
		element.textContent = target || '0';
		return;
	}
	
	let current = 0;
	const increment = target / 60; // Over ~1 second
	
	const updateCount = () => {
		current += increment;
		if (current < target) {
			element.textContent = Math.floor(current);
			requestAnimationFrame(updateCount);
		} else {
			element.textContent = Math.floor(target);
		}
	};
	
	updateCount();
}

// Intersection Observer for counter animation
if ("IntersectionObserver" in window) {
	const observerOptions = {
		threshold: 0.5
	};

	const counterObserver = new IntersectionObserver((entries) => {
		entries.forEach((entry) => {
			if (entry.isIntersecting && !entry.target.dataset.animated) {
				const target = parseInt(entry.target.getAttribute("data-target"));
				animateCounter(entry.target, target);
				entry.target.dataset.animated = "true";
			}
		});
	}, observerOptions);

	// Observe all counter elements - ONLY those with data-target attribute
	document.querySelectorAll(".stat-counter[data-target], .stat-number[data-target]").forEach((el) => {
		counterObserver.observe(el);
	});
}

// Smooth scroll with offset for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
	anchor.addEventListener('click', function (e) {
		const href = this.getAttribute('href');
		if (href !== '#') {
			e.preventDefault();
			const target = document.querySelector(href);
			if (target) {
				const offsetTop = target.offsetTop - 80;
				window.scrollTo({
					top: offsetTop,
					behavior: 'smooth'
				});
			}
		}
	});
});

// Add animation classes on scroll
function addScrollAnimations() {
	const elements = document.querySelectorAll("[data-aos]");
	
	if (!("IntersectionObserver" in window)) {
		elements.forEach(el => el.classList.add("aos-animate"));
		return;
	}

	const aosObserver = new IntersectionObserver((entries) => {
		entries.forEach((entry) => {
			if (entry.isIntersecting) {
				const element = entry.target;
				const animationType = element.getAttribute("data-aos");
				const delay = element.getAttribute("data-aos-delay") || "0";
				
				element.style.setProperty("--aos-delay", delay + "ms");
				element.classList.add("aos-animate", `aos-${animationType}`);
				aosObserver.unobserve(element);
			}
		});
	}, {
		threshold: 0.1
	});

	elements.forEach(el => aosObserver.observe(el));
}

// Add CSS for AOS animations
const aosStyles = `
	[data-aos] {
		opacity: 0;
		transition: opacity 0.6s ease, transform 0.6s ease;
	}

	[data-aos].aos-animate {
		opacity: 1;
	}

	.aos-fade-up {
		transform: translateY(30px);
	}

	.aos-fade-up.aos-animate {
		transform: translateY(0);
	}

	.aos-zoom-in {
		transform: scale(0.8);
	}

	.aos-zoom-in.aos-animate {
		transform: scale(1);
	}

	.aos-fade-in {
		opacity: 0;
	}

	.aos-fade-in.aos-animate {
		opacity: 1;
	}
`;

const styleSheet = document.createElement("style");
styleSheet.textContent = aosStyles;
document.head.appendChild(styleSheet);

// Initialize animations when DOM is ready
document.addEventListener("DOMContentLoaded", addScrollAnimations);

// Parallax effect for hero background (optional, subtle)
document.addEventListener("scroll", () => {
	const heroBackground = document.querySelector(".hero-background");
	if (heroBackground && window.scrollY < window.innerHeight) {
		const scrolled = window.scrollY;
		heroBackground.style.transform = `translateY(${scrolled * 0.5}px)`;
	}
}, { passive: true });

