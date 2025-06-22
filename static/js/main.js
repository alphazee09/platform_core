// Futuristic JavaScript for Mazin Yahia Platform

// Initialize platform on DOM load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize notifications first to make showNotification globally available
    initializeNotifications();
    
    // Then initialize other components
    initializePlatform();
    initializeAnimations();
    initializeInteractions();
    initializeFileUploads();
    initializeScrollEffects();
});

// Platform Initialization
function initializePlatform() {
    console.log('🚀 Platform Initialized');
    
    // Add page loading animation
    showPageLoader();
    
    // Add futuristic cursor effect
    createCursorEffect();
    
    // Initialize typing effects
    initializeTypingEffects();
    
    // Initialize particle background
    createParticleBackground();
    
    // Initialize smooth scroll
    initializeSmoothScroll();
    
    // Hide loader after initialization
    setTimeout(hidePageLoader, 1500);
    
    // Initialize interactive features
    initializeInteractiveFeatures();
}

function showPageLoader() {
    const loader = document.createElement('div');
    loader.className = 'page-loader';
    loader.innerHTML = `
        <div class="loader-content">
            <div class="loading-spinner"></div>
            <p class="loader-text">Initializing Platform...</p>
        </div>
    `;
    loader.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, #000000, #001122);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        opacity: 1;
        transition: opacity 0.5s ease;
    `;
    document.body.appendChild(loader);
}

function hidePageLoader() {
    const loader = document.querySelector('.page-loader');
    if (loader) {
        loader.style.opacity = '0';
        setTimeout(() => loader.remove(), 500);
    }
}

function initializeInteractiveFeatures() {
    // Animate statistics counters
    animateCounters();
    
    // Initialize interactive tutorial
    initializeTutorial();
    
    // Add scroll-triggered animations
    initializeScrollAnimations();
    
    // Initialize form interactions
    initializeFormInteractions();
    
    // Initialize character counters
    initializeCharacterCounters();
}

function animateCounters() {
    const counters = document.querySelectorAll('.stat-number');
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-count'));
        let current = 0;
        const increment = target / 50;
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                counter.textContent = target;
                clearInterval(timer);
            } else {
                counter.textContent = Math.floor(current);
            }
        }, 30);
    });
}

function initializeTutorial() {
    window.startTutorial = function() {
        const overlay = document.getElementById('tutorialOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
        
        // Start interactive walkthrough
        const steps = [
            { element: '.progress-steps', message: 'Track your progress through each step' },
            { element: '.form-section', message: 'Fill out each section with your project details' },
            { element: '.btn-wizard-next', message: 'Navigate between steps using these buttons' }
        ];
        
        highlightElements(steps, 0);
    };
    
    window.skipTutorial = function() {
        const overlay = document.getElementById('tutorialOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    };
}

function highlightElements(steps, index) {
    if (index >= steps.length) return;
    
    const step = steps[index];
    const element = document.querySelector(step.element);
    
    if (element) {
        element.classList.add('tutorial-highlight');
        showTutorialTooltip(element, step.message);
        
        setTimeout(() => {
            element.classList.remove('tutorial-highlight');
            highlightElements(steps, index + 1);
        }, 3000);
    }
}

function showTooltip(element, message) {
    if (!message) return;
    
    // Remove existing tooltips
    hideTooltips();
    
    const tooltip = document.createElement('div');
    tooltip.className = 'input-tooltip';
    tooltip.textContent = message;
    element.parentElement.appendChild(tooltip);
}

function showTutorialTooltip(element, message) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tutorial-tooltip';
    tooltip.textContent = message;
    element.appendChild(tooltip);
    
    setTimeout(() => tooltip.remove(), 2800);
}

function initializeScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });
}

function initializeFormInteractions() {
    // Add focus effects to form inputs
    const inputs = document.querySelectorAll('.form-control-futuristic');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('form-group-focused');
            showTooltip(this, this.getAttribute('data-tooltip'));
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('form-group-focused');
            hideTooltips();
        });
        
        input.addEventListener('input', function() {
            validateInput(this);
        });
    });
}

function validateInput(input) {
    const feedback = input.parentElement.querySelector('.input-feedback');
    const value = input.value.trim();
    
    if (input.hasAttribute('required') && value === '') {
        feedback.textContent = 'This field is required';
        feedback.className = 'input-feedback error';
        input.classList.add('is-invalid');
    } else if (value.length > 0) {
        feedback.textContent = 'Looks good!';
        feedback.className = 'input-feedback success';
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
    } else {
        feedback.textContent = '';
        feedback.className = 'input-feedback';
        input.classList.remove('is-invalid', 'is-valid');
    }
}

function initializeCharacterCounters() {
    const textareas = document.querySelectorAll('textarea[data-tooltip]');
    textareas.forEach(textarea => {
        const counter = textarea.parentElement.querySelector('.char-counter');
        if (counter) {
            const currentSpan = counter.querySelector('.current');
            const maxSpan = counter.querySelector('.max');
            const maxLength = parseInt(maxSpan.textContent);
            
            textarea.addEventListener('input', function() {
                const length = this.value.length;
                currentSpan.textContent = length;
                
                if (length > maxLength * 0.9) {
                    counter.classList.add('warning');
                } else {
                    counter.classList.remove('warning');
                }
                
                if (length > maxLength) {
                    counter.classList.add('error');
                } else {
                    counter.classList.remove('error');
                }
            });
        }
    });
}

function hideTooltips() {
    document.querySelectorAll('.input-tooltip, .tutorial-tooltip').forEach(tooltip => {
        tooltip.remove();
    });
}

// Optimized Cursor Effect
function createCursorEffect() {
    const cursor = document.createElement('div');
    cursor.className = 'custom-cursor';
    cursor.innerHTML = '<div class="cursor-dot"></div><div class="cursor-ring"></div>';
    document.body.appendChild(cursor);
    
    let isMoving = false;
    
    // Use throttled mousemove for better performance
    document.addEventListener('mousemove', throttle((e) => {
        cursor.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
    }, 16)); // ~60fps
    
    // Add hover effects for interactive elements
    const interactiveElements = document.querySelectorAll('a, button, [data-cursor="pointer"]');
    interactiveElements.forEach(el => {
        el.addEventListener('mouseenter', () => cursor.classList.add('cursor-hover'));
        el.addEventListener('mouseleave', () => cursor.classList.remove('cursor-hover'));
    });
    
    // Add optimized CSS for cursor
    const cursorStyle = document.createElement('style');
    cursorStyle.textContent = `
        .custom-cursor {
            position: fixed;
            top: 0;
            left: 0;
            pointer-events: none;
            z-index: 9999;
            mix-blend-mode: difference;
            will-change: transform;
            transform: translate(-50%, -50%);
        }
        
        .cursor-dot {
            width: 8px;
            height: 8px;
            background: #00ff88;
            border-radius: 50%;
            transition: transform 0.1s ease;
        }
        
        .cursor-ring {
            position: absolute;
            top: -11px;
            left: -11px;
            width: 22px;
            height: 22px;
            border: 2px solid rgba(0, 255, 136, 0.3);
            border-radius: 50%;
            transition: transform 0.2s ease;
        }
        
        .cursor-hover .cursor-dot {
            transform: scale(1.5);
        }
        
        .cursor-hover .cursor-ring {
            transform: scale(2);
            border-color: rgba(0, 255, 136, 0.6);
        }
        
        @media (pointer: coarse) {
            .custom-cursor { display: none; }
        }
    `;
    document.head.appendChild(cursorStyle);
}

// Typing Effect Animation
function initializeTypingEffects() {
    const typeElements = document.querySelectorAll('.typing-effect');
    
    typeElements.forEach(element => {
        const text = element.textContent;
        element.textContent = '';
        element.style.opacity = '1';
        
        typeText(element, text, 0);
    });
}

function typeText(element, text, index) {
    if (index < text.length) {
        element.textContent += text.charAt(index);
        setTimeout(() => typeText(element, text, index + 1), 100);
    } else {
        // Add blinking cursor
        const cursor = document.createElement('span');
        cursor.className = 'typing-cursor';
        cursor.textContent = '|';
        cursor.style.animation = 'blink 1s infinite';
        element.appendChild(cursor);
    }
}

// Particle Background
function createParticleBackground() {
    const canvas = document.createElement('canvas');
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '-2';
    canvas.style.pointerEvents = 'none';
    document.body.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    let particles = [];
    
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    function createParticles() {
        particles = [];
        const particleCount = Math.floor((canvas.width * canvas.height) / 15000);
        
        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                size: Math.random() * 2 + 1,
                opacity: Math.random() * 0.5 + 0.1,
                color: `hsl(${Math.random() * 60 + 140}, 100%, 50%)`
            });
        }
    }
    
    function animateParticles() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        particles.forEach((particle, index) => {
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -1;
            if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -1;
            
            ctx.save();
            ctx.globalAlpha = particle.opacity;
            ctx.fillStyle = particle.color;
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
            
            // Connect nearby particles
            particles.slice(index + 1).forEach(otherParticle => {
                const dx = particle.x - otherParticle.x;
                const dy = particle.y - otherParticle.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 100) {
                    ctx.save();
                    ctx.globalAlpha = (100 - distance) / 100 * 0.2;
                    ctx.strokeStyle = '#00ff88';
                    ctx.lineWidth = 0.5;
                    ctx.beginPath();
                    ctx.moveTo(particle.x, particle.y);
                    ctx.lineTo(otherParticle.x, otherParticle.y);
                    ctx.stroke();
                    ctx.restore();
                }
            });
        });
        
        requestAnimationFrame(animateParticles);
    }
    
    resizeCanvas();
    createParticles();
    animateParticles();
    
    window.addEventListener('resize', () => {
        resizeCanvas();
        createParticles();
    });
}

// Smooth Scrolling
function initializeSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Animation System
function initializeAnimations() {
    // Intersection Observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                
                // Stagger animations for children
                const children = entry.target.querySelectorAll('.animate-child');
                children.forEach((child, index) => {
                    setTimeout(() => {
                        child.classList.add('animate-in');
                    }, index * 100);
                });
            }
        });
    }, observerOptions);
    
    // Observe all animatable elements
    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });
    
    // Add CSS for animations
    const animationStyle = document.createElement('style');
    animationStyle.textContent = `
        .animate-on-scroll {
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .animate-on-scroll.animate-in {
            opacity: 1;
            transform: translateY(0);
        }
        
        .animate-child {
            opacity: 0;
            transform: translateX(-20px);
            transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .animate-child.animate-in {
            opacity: 1;
            transform: translateX(0);
        }
        
        .typing-cursor {
            color: #00ff88;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
    `;
    document.head.appendChild(animationStyle);
}

// Interactive Elements
function initializeInteractions() {
    // Holographic card effects
    document.querySelectorAll('.glass-card').forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = (y - centerY) / 10;
            const rotateY = (centerX - x) / 10;
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(10px)`;
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
        });
    });
    
    // Button ripple effects
    document.querySelectorAll('.btn-futuristic, .btn-outline-futuristic').forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s ease-out;
                pointer-events: none;
            `;
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
    
    // Add ripple animation CSS
    const rippleStyle = document.createElement('style');
    rippleStyle.textContent = `
        @keyframes ripple {
            to {
                transform: scale(2);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(rippleStyle);
}

// File Upload System
function initializeFileUploads() {
    const uploadAreas = document.querySelectorAll('.file-upload-area');
    
    uploadAreas.forEach(area => {
        const input = area.querySelector('input[type="file"]');
        
        area.addEventListener('dragover', (e) => {
            e.preventDefault();
            area.classList.add('dragover');
        });
        
        area.addEventListener('dragleave', () => {
            area.classList.remove('dragover');
        });
        
        area.addEventListener('drop', (e) => {
            e.preventDefault();
            area.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (input && files.length > 0) {
                input.files = files;
                handleFileUpload(files, area);
            }
        });
        
        area.addEventListener('click', () => {
            if (input) input.click();
        });
        
        if (input) {
            input.addEventListener('change', (e) => {
                handleFileUpload(e.target.files, area);
            });
        }
    });
}

function handleFileUpload(files, area) {
    const fileList = area.querySelector('.file-list') || createFileList(area);
    
    Array.from(files).forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item glass-card';
        fileItem.style.cssText = `
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1rem;
            margin: 0.5rem 0;
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid rgba(0, 255, 136, 0.3);
        `;
        
        fileItem.innerHTML = `
            <div>
                <i class="fas fa-file"></i>
                <span>${file.name}</span>
                <small>(${formatFileSize(file.size)})</small>
            </div>
            <div class="progress-futuristic" style="width: 200px;">
                <div class="progress-bar-futuristic" style="width: 0%"></div>
            </div>
        `;
        
        fileList.appendChild(fileItem);
        
        // Simulate upload progress
        simulateUploadProgress(fileItem.querySelector('.progress-bar-futuristic'));
    });
}

function createFileList(area) {
    const fileList = document.createElement('div');
    fileList.className = 'file-list';
    area.appendChild(fileList);
    return fileList;
}

function simulateUploadProgress(progressBar) {
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
        }
        progressBar.style.width = progress + '%';
    }, 200);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Notification System
function initializeNotifications() {
    // Create notification container if it doesn't exist
    if (!document.getElementById('notification-container')) {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
        `;
        document.body.appendChild(container);
    }

    // Define showNotification globally
    window.showNotification = function(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            background: ${type === 'success' ? 'var(--success-color)' : 
                        type === 'error' ? 'var(--error-color)' : 
                        type === 'warning' ? 'var(--warning-color)' : 'var(--info-color)'};
            color: var(--dark-bg);
            padding: 1rem;
            margin-bottom: 0.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            animation: slideInRight 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-weight: 600;
        `;
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-${getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button onclick="this.parentElement.remove()" style="background: none; border: none; color: inherit; cursor: pointer; padding: 0; margin-left: 10px;">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        const container = document.getElementById('notification-container');
        if (container) {
            container.appendChild(notification);
            
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.style.animation = 'slideOutRight 0.3s ease forwards';
                    setTimeout(() => notification.remove(), 300);
                }
            }, duration);
        }
    };
    
    // Handle flash messages
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        const type = message.classList.contains('alert-success') ? 'success' :
                    message.classList.contains('alert-danger') ? 'error' :
                    message.classList.contains('alert-warning') ? 'warning' : 'info';
        
        if (typeof window.showNotification === 'function') {
            window.showNotification(message.textContent.trim(), type);
            message.remove();
        }
    });
}

function getNotificationIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Scroll Effects
function initializeScrollEffects() {
    let ticking = false;
    
    function updateScrollEffects() {
        const scrolled = window.pageYOffset;
        const rate = scrolled * -0.5;
        
        // Parallax effect for hero section
        const hero = document.querySelector('.hero-section');
        if (hero) {
            hero.style.transform = `translateY(${rate}px)`;
        }
        
        // Navbar background opacity
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            const opacity = Math.min(scrolled / 100, 0.95);
            navbar.style.background = `rgba(10, 10, 10, ${opacity})`;
        }
        
        ticking = false;
    }
    
    function requestScrollUpdate() {
        if (!ticking) {
            requestAnimationFrame(updateScrollEffects);
            ticking = true;
        }
    }
    
    window.addEventListener('scroll', requestScrollUpdate);
}

// AJAX Form Handling
function initializeAjaxForms() {
    const forms = document.querySelectorAll('.ajax-form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            
            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message || 'Operation completed successfully', 'success');
                    if (data.redirect) {
                        setTimeout(() => window.location.href = data.redirect, 1000);
                    }
                } else {
                    showNotification(data.message || 'An error occurred', 'error');
                }
            })
            .catch(error => {
                showNotification('Network error occurred', 'error');
                console.error('Error:', error);
            })
            .finally(() => {
                // Restore button state
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            });
        });
    });
}

// Real-time Updates
function initializeRealTimeUpdates() {
    // Check for new messages
    setInterval(() => {
        updateMessageCount();
        updateNotificationCount();
    }, 30000); // Check every 30 seconds
}

function updateMessageCount() {
    fetch('/api/unread-messages')
        .then(response => response.json())
        .then(data => {
            const badge = document.querySelector('.message-count-badge');
            if (badge && data.count > 0) {
                badge.textContent = data.count;
                badge.style.display = 'inline';
            } else if (badge) {
                badge.style.display = 'none';
            }
        })
        .catch(error => console.error('Error updating message count:', error));
}

function updateNotificationCount() {
    fetch('/api/notifications')
        .then(response => response.json())
        .then(data => {
            const badge = document.querySelector('.notification-count-badge');
            if (badge && data.count > 0) {
                badge.textContent = data.count;
                badge.style.display = 'inline';
            } else if (badge) {
                badge.style.display = 'none';
            }
        })
        .catch(error => console.error('Error updating notification count:', error));
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Initialize additional features when page is loaded
window.addEventListener('load', function() {
    initializeAjaxForms();
    initializeRealTimeUpdates();
    
    // Add loading complete class
    document.body.classList.add('loaded');
    
    // Hide any loading screens
    const loader = document.querySelector('.page-loader');
    if (loader) {
        loader.style.opacity = '0';
        setTimeout(() => loader.remove(), 500);
    }
});

// Make showNotification globally available immediately
window.showNotification = function(message, type = 'info', duration = 5000) {
    console.log(`Notification: ${message}`);
};

// Export functions for global use
window.PlatformJS = {
    showNotification: window.showNotification,
    formatFileSize,
    debounce,
    throttle
};
