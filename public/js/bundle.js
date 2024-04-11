/*******************************************************************************
 * Theme interaction
 */

var prefersDark = window.matchMedia("(prefers-color-scheme: dark)");

/**
 * set the the body theme to the one specified by the user browser
 *
 * @param {event} e
 */
function setTheme() {
  /* One of auto, light, or dark, depending on what the site wants to support */
  const themeScheme = document.documentElement.getAttribute("data-colorscheme");

  const browserScheme = prefersDark.matches ? "dark" : "light";

  // Use the color scheme from the configuration file, if set
  document.documentElement.setAttribute(
    "data-theme",
    themeScheme == "auto" ? browserScheme : themeScheme,
  );
}

setTheme();
prefersDark.onchange = setTheme;

;
// copy-code-blocks.js

// This file implements a button attached to code blocks which copies
// the code to the clipboard.

// This selector should match the PRE elements, each of which may
// itself contain the text to be copied, or may contain a CODE element
// which contains the text to be copied.
const pre_selector = "div.highlight pre";

document.querySelectorAll(pre_selector).forEach(add_button_to);

function add_button_to(element) {
  div = document.createElement("div");
  button = document.createElement("button");
  div.classList.add("copy-button");
  button.addEventListener("click", copy_content_of);
  div.append(button);
  element.prepend(div);
}

function copy_content_of(event) {
  content = this.parentElement.parentElement.textContent + "\n";
  navigator.clipboard.writeText(content).then(() => update_button(this));
}

function update_button(button, clicked_class = "clicked", timeout_ms = 2000) {
  button.classList.add(clicked_class);
  setTimeout(() => button.classList.remove(clicked_class), timeout_ms);
}

// copy-code-blocks.js ends.

;
function whenReady() {
  //Mobile menu toggle
  const burgers = document.getElementsByClassName("navbar-burger");
  if (burgers) {
    Array.prototype.map.call(burgers, (burger) => {
      burger.addEventListener("click", () => {
        burger.classList.toggle("is-active");

        const menu_id = burger.getAttribute("data-target");
        const menu = document.getElementById(menu_id);
        menu.classList.toggle("is-active");
      });
    });
  }

  // Back to Top button behaviour
  const pxShow = 600;
  var timer = null;
  const backToTop = document.getElementById("backtotop");

  window.addEventListener("scroll", () => {
    const scrollTop = document.documentElement.scrollTop;

    if (timer !== null) {
      clearTimeout(timer);
    }

    timer = setTimeout(() =>
      backToTop.classList.toggle("visible", scrollTop >= pxShow),
    );
  });

  backToTop.addEventListener("click", () => {
    window.scrollTo({ top: 500, behavior: "smooth" });
  });
}

if (document.readyState !== "loading") {
  whenReady();
} else {
  document.addEventListener("DOMContentLoaded", whenReady);
}

;
// throttle function, enforces a minimum time interval
function throttle(fn, interval) {
  var lastCall, timeoutId;
  return function () {
    var now = new Date().getTime();
    if (lastCall && now < lastCall + interval) {
      // if we are inside the interval we remove
      // the existing timer and set up a new one
      clearTimeout(timeoutId);
      timeoutId = setTimeout(
        function () {
          lastCall = now;
          fn.call();
        },
        interval - (now - lastCall),
      );
    } else {
      // otherwise, we directly call the function
      lastCall = now;
      fn.call();
    }
  };
}

// Highlight currently scrolled to header in shortcuts
// Based on https://stackoverflow.com/a/32396543/214686
// and
// https://stackoverflow.com/a/57494988/214686
// which fixes some issues with the first, particularly
// around scrolling upward.
function scrollHeaders() {
  const scrollPosition = document.documentElement.scrollTop;
  const headers = Array.from(
    document.querySelectorAll(":is(h1, h2, h3, h4, h5, h6)[id]"),
  );
  const allShortcuts = Array.from(
    document.querySelectorAll("#shortcuts > div"),
  );

  headers.map((currentSection) => {
    // get the position of the section
    // emulates JQuery's .position().top
    const marginTop = parseInt(getComputedStyle(currentSection).marginTop, 10);
    var sectionTop = currentSection.offsetTop - marginTop;
    var sectionHeight = currentSection.getBoundingClientRect().height;
    var overall = scrollPosition + sectionHeight;
    var headerOffset = remToPx(4);

    if (scrollPosition < headerOffset) {
      allShortcuts.map((shortcut) => shortcut.classList.remove("active"));
      return;
    }

    // user has scrolled over the top of the section
    if (
      scrollPosition + headerOffset >= sectionTop &&
      scrollPosition < overall
    ) {
      const id = currentSection.id;
      const shortcut = document.getElementById(`${id}-shortcut`);
      if (shortcut) {
        allShortcuts.map((shortcut) => shortcut.classList.remove("active"));
        shortcut.classList.add("active");
      }
    }
  });
}

const throttledScrollHeaders = throttle(scrollHeaders, 100);

function bindScroll() {
  window.addEventListener("scroll", throttledScrollHeaders);
}

function unbindScroll() {
  window.removeEventListener("scroll", throttledScrollHeaders);
}

function remToPx(rem) {
  return rem * parseFloat(getComputedStyle(document.documentElement).fontSize);
}

function setupShortcuts(shortcutDepth = 2) {
  shortcutDepth += 1; // to account for the page title

  // Build a class selector for each header type, and concatenate with commas
  let classes = "";
  for (let i = 2; i <= shortcutDepth; i++) {
    if (i != 2) {
      classes += ",";
    }
    classes += " .content-container :not([role='tabpanel']) > h" + i;
  }

  // Content Page Shortcuts
  const shortcutsTarget = document.getElementById("shortcuts");
  if (shortcutsTarget) {
    const classElements = Array.from(document.querySelectorAll(classes));
    classElements.map((el) => {
      const title = el.innerHTML;
      const elId = el.id;
      // Gets the element type (e.g. h2, h3)
      const elType = el.tagName;
      // Adds snake-case title as an id attribute to target element
      shortcutsTarget.insertAdjacentHTML(
        "beforeend",
        `<div id="${elId}-shortcut" class="shortcuts-${elType}" href="#${elId}">${title}</div>`,
      );

      const shortcut = document.getElementById(`${elId}-shortcut`);
      shortcut.addEventListener("click", () => {
        event.preventDefault();

        // We don't want the shortcuts to flash through highlights while
        // we scroll to the desired header
        unbindScroll();

        // Replace what's in the location bar, without changing browser history
        // and without triggering a page scroll
        history.replaceState(null, null, `#${elId}`);
        const shortcutDivs = Array.from(
          document.querySelectorAll("#shortcuts > div"),
        );
        shortcutDivs.forEach((e) => e.classList.remove("active"));
        shortcut.classList.add("active");

        let headerOffset = el.offsetTop - 60;
        scrollToThen(headerOffset, () => {
          // Done moving to clicked header; re-enable
          // scroll highlighting of shortcuts
          bindScroll();
        });
      });
    });
  }

  // Removes the shortcuts container if no shortcuts exist.
  // Also removes the 'Get Help' link.
  const shortcuts = Array.from(
    document.querySelectorAll("#shortcuts div:not(#shortcuts-header)"),
  );
  if (shortcuts.length == 0) {
    const shortcutsContainer = document.getElementById("shortcuts-container");
    if (shortcutsContainer) {
      shortcutsContainer.style.display = "none";
    }
  }

  bindScroll();
}

/**
 * Modified from https://stackoverflow.com/a/55686711/214686
 */
function scrollToThen(offset, callback) {
  const onScroll = throttle(() => {
    const fixedOffset = offset.toFixed();
    if (window.pageYOffset.toFixed() === fixedOffset) {
      window.removeEventListener("scroll", onScroll);
      callback();
    }
  }, 100);

  window.addEventListener("scroll", onScroll);
  onScroll();
  window.scrollTo({
    top: offset,
    /* behavior: 'smooth' */ /* too slow? */
  });
}

;
/* From https://www.w3.org/WAI/ARIA/apg/patterns/tabs/examples/tabs-automatic/ */

/*
 *   This content is licensed according to the W3C Software License at
 *   https://www.w3.org/Consortium/Legal/2015/copyright-software-and-document
 *
 *   File:   tabs-automatic.js
 *
 *   Desc:   Tablist widget that implements ARIA Authoring Practices
 */

"use strict";

class TabsAutomatic {
  constructor(groupNode) {
    this.tablistNode = groupNode;

    this.tabs = [];

    this.firstTab = null;
    this.lastTab = null;

    this.tabs = Array.from(this.tablistNode.querySelectorAll("[role=tab]"));
    this.tabpanels = [];

    for (var i = 0; i < this.tabs.length; i += 1) {
      var tab = this.tabs[i];
      var tabpanel = document.getElementById(tab.getAttribute("aria-controls"));

      tab.tabIndex = -1;
      tab.setAttribute("aria-selected", "false");
      this.tabpanels.push(tabpanel);

      tab.addEventListener("keydown", this.onKeydown.bind(this));
      tab.addEventListener("click", this.onClick.bind(this));

      if (!this.firstTab) {
        this.firstTab = tab;
      }
      this.lastTab = tab;
    }

    this.setSelectedTab(this.firstTab, false);
  }

  setSelectedTab(currentTab, setFocus) {
    if (typeof setFocus !== "boolean") {
      setFocus = true;
    }
    for (var i = 0; i < this.tabs.length; i += 1) {
      var tab = this.tabs[i];
      if (currentTab === tab) {
        tab.setAttribute("aria-selected", "true");
        tab.removeAttribute("tabindex");
        this.tabpanels[i].classList.remove("is-hidden");
        if (setFocus) {
          tab.focus();
        }
      } else {
        tab.setAttribute("aria-selected", "false");
        tab.tabIndex = -1;
        this.tabpanels[i].classList.add("is-hidden");
      }
    }
  }

  setSelectedToPreviousTab(currentTab) {
    var index;

    if (currentTab === this.firstTab) {
      this.setSelectedTab(this.lastTab);
    } else {
      index = this.tabs.indexOf(currentTab);
      this.setSelectedTab(this.tabs[index - 1]);
    }
  }

  setSelectedToNextTab(currentTab) {
    var index;

    if (currentTab === this.lastTab) {
      this.setSelectedTab(this.firstTab);
    } else {
      index = this.tabs.indexOf(currentTab);
      this.setSelectedTab(this.tabs[index + 1]);
    }
  }

  /* EVENT HANDLERS */

  onKeydown(event) {
    var tgt = event.currentTarget,
      flag = false;

    switch (event.key) {
      case "ArrowLeft":
        this.setSelectedToPreviousTab(tgt);
        flag = true;
        break;

      case "ArrowRight":
        this.setSelectedToNextTab(tgt);
        flag = true;
        break;

      case "Home":
        this.setSelectedTab(this.firstTab);
        flag = true;
        break;

      case "End":
        this.setSelectedTab(this.lastTab);
        flag = true;
        break;

      default:
        break;
    }

    if (flag) {
      event.stopPropagation();
      event.preventDefault();
    }
  }

  onClick(event) {
    this.setSelectedTab(event.currentTarget);
  }
}

// Initialize tablist

window.addEventListener("load", function () {
  var tablists = document.querySelectorAll("[role=tablist].automatic");
  for (var i = 0; i < tablists.length; i++) {
    new TabsAutomatic(tablists[i]);
  }
});
