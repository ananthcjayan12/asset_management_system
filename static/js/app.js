/* Small progressive enhancements shared by the application templates. */
(function () {
  "use strict";
  if (window.__appEnhancements) return;
  window.__appEnhancements = true;

  // select[data-searchable]: adds a "type to search" box that narrows the options.
  function enhanceSelect(select) {
    select.setAttribute("data-search-ready", "");
    var all = Array.prototype.map.call(select.options, function (o) { return o; });
    var box = document.createElement("input");
    box.type = "search";
    box.className = "form-control form-control-sm select-search";
    box.placeholder = "Type to search…";
    box.setAttribute("aria-label", "Search " + (select.labels && select.labels[0] ? select.labels[0].textContent.replace(/:$/, "") : "options"));
    select.insertAdjacentElement("beforebegin", box);
    box.addEventListener("input", function () {
      var terms = box.value.toLowerCase().split(/\s+/).filter(Boolean);
      var previous = select.value;
      select.innerHTML = "";
      all.forEach(function (o) {
        var text = o.text.toLowerCase();
        if (!o.value || terms.every(function (t) { return text.indexOf(t) !== -1; })) select.appendChild(o);
      });
      var matches = Array.prototype.filter.call(select.options, function (o) { return o.value; });
      if (terms.length && matches.length && !matches.some(function (o) { return o.value === previous; })) {
        select.value = matches[0].value;
      } else {
        select.value = previous;
      }
      if (select.value !== previous) select.dispatchEvent(new Event("change", { bubbles: true }));
    });
  }

  // [data-filter-target="#id"]: filters the labelled checkboxes/rows inside the target.
  function enhanceFilter(box) {
    box.setAttribute("data-filter-ready", "");
    box.addEventListener("input", function () {
      var target = document.querySelector(box.getAttribute("data-filter-target"));
      if (!target) return;
      var terms = box.value.toLowerCase().split(/\s+/).filter(Boolean);
      target.querySelectorAll("[data-filter-item]").forEach(function (item) {
        var text = item.textContent.toLowerCase();
        item.style.display = terms.every(function (t) { return text.indexOf(t) !== -1; }) ? "" : "none";
      });
    });
  }

  function enhance(root) {
    root = root || document;
    root.querySelectorAll("select[data-searchable]:not([data-search-ready])").forEach(enhanceSelect);
    root.querySelectorAll("[data-filter-target]:not([data-filter-ready])").forEach(enhanceFilter);
  }

  document.addEventListener("htmx:afterSwap", function (e) { enhance(e.target); });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { enhance(); });
  else enhance();
})();
