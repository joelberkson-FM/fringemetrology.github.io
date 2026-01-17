document.addEventListener('DOMContentLoaded', () => {
    // Select all dropdowns interacting with carousels (future proofing)
    const dropdowns = document.querySelectorAll('.dropdown');

    dropdowns.forEach(dropdown => {
        const track = dropdown.querySelector('.carousel-track');
        if (!track) return;

        // Simple auto-scroll functionality or interaction
        // For now, let's implement a gentle auto-scroll on hover that pauses

        let scrollAmount = 0;
        let isPaused = false;

        // Clone items for infinite effect if needed, but for MVP let's just do a simple pan
        // Actually, user requested "carousel", often implies click to slide or auto slide
        // Let's adding Next/Prev buttons dynamically if needed, or just let it be a static grid for now
        // if user didn't specify interaction details.
        // Re-reading: "carousel displays... convey sleek and modern"

        // Let's add a slow drift effect that speeds up on mouse move?
        // Or just standard "hover to see details".

        // Let's implement a basic manual slide on mouse wheel if in dropdown, 
        // to feel 'app-like'

        dropdown.addEventListener('wheel', (e) => {
            e.preventDefault();
            track.scrollLeft += e.deltaY;
        });
    });

    const header = document.querySelector('header');

    window.addEventListener('scroll', () => {
        if (document.body.classList.contains('subpage')) {
            // Always keep header in scrolled state for subpages
            header.classList.add('scrolled');
            return;
        }

        if (window.scrollY > 100) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });

    const heroBg = document.getElementById('hero-bg');
    if (heroBg) {
        // Delay slightly to ensure initial paint happens first
        setTimeout(() => {
            const iframe = document.createElement('iframe');
            iframe.src = "https://player.vimeo.com/video/721266614?muted=1&autoplay=1&loop=1&background=1&app_id=122963";
            iframe.setAttribute('frameborder', '0');
            iframe.setAttribute('allow', 'autoplay; fullscreen; picture-in-picture');
            iframe.setAttribute('allowfullscreen', '');
            iframe.setAttribute('title', 'Header Video');
            heroBg.appendChild(iframe);
        }, 500);
    }

    const mobileNavToggle = document.querySelector('.mobile-nav-toggle');
    const nav = document.querySelector('nav');
    const body = document.body;

    if (mobileNavToggle && nav) {
        mobileNavToggle.addEventListener('click', () => {
            mobileNavToggle.classList.toggle('active');
            nav.classList.toggle('active');
            body.classList.toggle('no-scroll');
        });

        // Close menu when a link is clicked
        const navLinks = nav.querySelectorAll('a');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                mobileNavToggle.classList.remove('active');
                nav.classList.remove('active');
                body.classList.remove('no-scroll');
            });
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // File upload handling
    const fileInput = document.getElementById('file-upload');
    const fileNameDisplay = document.getElementById('file-name-display');

    if (fileInput && fileNameDisplay) {
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                // Check size (16.78MB = 16.78 * 1024 * 1024 bytes approx 17595280)
                const maxSize = 16.78 * 1024 * 1024;
                if (file.size > maxSize) {
                    alert('File is too large. Maximum size is 16.78MB.');
                    fileInput.value = ''; // Clear selection
                    fileNameDisplay.textContent = 'File Supporting Files';
                } else {
                    fileNameDisplay.textContent = file.name;
                }
            } else {
                fileNameDisplay.textContent = 'File Supporting Files';
            }
        });
    }

    console.log("Fringe Metrology site loaded. Animations ready.");

    // Blog Filtering
    const filterBtns = document.querySelectorAll('.filter-btn');
    const blogCards = document.querySelectorAll('.blog-card');

    if (filterBtns.length > 0) {
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                // Remove active class from all
                filterBtns.forEach(b => b.classList.remove('active'));
                // Add active to clicked
                btn.classList.add('active');

                const filter = btn.getAttribute('data-filter');

                blogCards.forEach(card => {
                    const type = card.getAttribute('data-type');

                    if (filter === 'all' || type === filter) {
                        card.style.display = 'flex';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        });
    }
});
