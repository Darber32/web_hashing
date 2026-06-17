
function open_modal(modalId){

    const modal = document.getElementById(modalId)
    
    modal.classList.add("active")
    
    document.body.style.overflow = "hidden"
    
    
    modal.addEventListener("click", function(e){
    
        if(e.target === modal){
            close_modal(modalId)
        }
    
    })
    
}
    
function close_modal(modalId){
    
    const modal = document.getElementById(modalId)
    
    modal.classList.remove("active")
    
    document.body.style.overflow = "auto"
    
}

function close_error() {
    const alertNode = document.getElementById('error-alert');

    if(alertNode){
        alertNode.style.display = 'none';
    }
}

const THEME_STORAGE_KEY = 'hash-theme';
const THEME_COLOR_MAP = {
    light: '#eef2f7',
    dark: '#0f1318',
};

function get_preferred_theme(){
    const storedTheme = localStorage.getItem(THEME_STORAGE_KEY);

    if(storedTheme === 'light' || storedTheme === 'dark'){
        return storedTheme;
    }

    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function update_theme_color(theme){
    const themeColorMeta = document.getElementById('theme-color-meta');

    if(themeColorMeta){
        themeColorMeta.setAttribute('content', THEME_COLOR_MAP[theme] || THEME_COLOR_MAP.light);
    }
}

function update_theme_toggle(theme){
    const themeToggle = document.querySelector('.navbar__theme-toggle');

    if(!themeToggle){
        return;
    }

    const themeLabel = themeToggle.querySelector('[data-theme-label]');
    const isDarkTheme = theme === 'dark';

    themeToggle.setAttribute('aria-pressed', isDarkTheme ? 'true' : 'false');
    themeToggle.setAttribute(
        'aria-label',
        isDarkTheme ? 'Переключить на светлую тему' : 'Переключить на тёмную тему',
    );

    if(themeLabel){
        themeLabel.textContent = isDarkTheme ? 'Тёмная тема' : 'Светлая тема';
    }
}

function apply_theme(theme){
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.style.colorScheme = theme === 'dark' ? 'dark' : 'light';
    update_theme_color(theme);
    update_theme_toggle(theme);
}

function toggle_theme(){
    const currentTheme = document.documentElement.getAttribute('data-theme') || get_preferred_theme();
    const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';

    localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
    apply_theme(nextTheme);
}

function toggle_navbar(){
    const header = document.querySelector('.site-header');
    const toggle = document.querySelector('.navbar__toggle');

    if(!header || !toggle){
        return;
    }

    const isOpen = header.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
}

function close_navbar(){
    const header = document.querySelector('.site-header');
    const toggle = document.querySelector('.navbar__toggle');

    if(!header || !toggle){
        return;
    }

    header.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
}

document.addEventListener('click', function(event){
    const header = document.querySelector('.site-header');

    if(!header || !header.classList.contains('is-open')){
        return;
    }

    if(!header.contains(event.target)){
        close_navbar();
    }
});

window.addEventListener('resize', function(){
    if(window.innerWidth > 900){
        close_navbar();
    }
});

document.addEventListener('DOMContentLoaded', function(){
    apply_theme(document.documentElement.getAttribute('data-theme') || get_preferred_theme());
});
