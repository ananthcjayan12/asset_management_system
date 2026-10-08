/* Compact date picker for input[data-datepicker] fields (dd-mm-yyyy).
 * The calendar button sits directly beside the field and the popup offers
 * month/year drop-downs and previous/next-year buttons for year-wise navigation. */
(function () {
  "use strict";
  if (window.__appDatepicker) return;
  window.__appDatepicker = true;

  var MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  var popup = null, input = null, view = null;

  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function format(d) { return pad(d.getDate()) + "-" + pad(d.getMonth() + 1) + "-" + d.getFullYear(); }
  function parse(value) {
    var v = (value || "").trim(), m = /^(\d{1,2})[-\/.](\d{1,2})[-\/.](\d{4})$/.exec(v);
    if (m) return new Date(+m[3], +m[2] - 1, +m[1]);
    m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(v);
    if (m) return new Date(+m[1], +m[2] - 1, +m[3]);
    return null;
  }
  function sameDay(a, b) { return a && b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate(); }

  function close() {
    if (popup) popup.remove();
    popup = input = view = null;
  }

  function setValue(date) {
    input.value = date ? format(date) : "";
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
    input.focus();
    close();
  }

  function render() {
    var year = view.getFullYear(), month = view.getMonth(), thisYear = new Date().getFullYear();
    var first = Math.min(1950, year), last = Math.max(thisYear + 15, year);
    var html = '<div class="dp-head">' +
      '<button type="button" data-nav="-12" title="Previous year" aria-label="Previous year">&laquo;</button>' +
      '<button type="button" data-nav="-1" title="Previous month" aria-label="Previous month">&lsaquo;</button>' +
      '<select class="dp-month" aria-label="Month">';
    MONTHS.forEach(function (name, i) { html += '<option value="' + i + '"' + (i === month ? " selected" : "") + ">" + name.slice(0, 3) + "</option>"; });
    html += '</select><select class="dp-year" aria-label="Year">';
    for (var y = last; y >= first; y--) html += '<option value="' + y + '"' + (y === year ? " selected" : "") + ">" + y + "</option>";
    html += '</select>' +
      '<button type="button" data-nav="1" title="Next month" aria-label="Next month">&rsaquo;</button>' +
      '<button type="button" data-nav="12" title="Next year" aria-label="Next year">&raquo;</button></div>' +
      '<table class="dp-grid"><thead><tr><th>S</th><th>M</th><th>T</th><th>W</th><th>T</th><th>F</th><th>S</th></tr></thead><tbody><tr>';
    var start = new Date(year, month, 1).getDay(), days = new Date(year, month + 1, 0).getDate();
    var selected = parse(input.value), today = new Date(), cell = 0;
    for (; cell < start; cell++) html += "<td></td>";
    for (var d = 1; d <= days; d++, cell++) {
      if (cell && cell % 7 === 0) html += "</tr><tr>";
      var date = new Date(year, month, d), cls = [];
      if (sameDay(date, selected)) cls.push("dp-selected");
      if (sameDay(date, today)) cls.push("dp-today");
      html += '<td><button type="button" data-day="' + d + '" class="' + cls.join(" ") + '">' + d + "</button></td>";
    }
    for (; cell % 7; cell++) html += "<td></td>";
    html += '</tr></tbody></table><div class="dp-foot">' +
      '<button type="button" data-action="today">Today</button>' +
      '<button type="button" data-action="clear">Clear</button>' +
      '<button type="button" data-action="close">Close</button></div>';
    popup.innerHTML = html;
  }

  function position() {
    var r = input.getBoundingClientRect();
    popup.style.top = window.scrollY + r.bottom + 4 + "px";
    popup.style.left = Math.max(8, Math.min(window.scrollX + r.left, window.scrollX + document.documentElement.clientWidth - popup.offsetWidth - 8)) + "px";
  }

  function open(target) {
    if (input === target) return;
    close();
    input = target;
    var d = parse(input.value) || new Date();
    view = new Date(d.getFullYear(), d.getMonth(), 1);
    popup = document.createElement("div");
    popup.className = "dp-popup";
    popup.setAttribute("role", "dialog");
    popup.addEventListener("mousedown", function (e) { if (e.target.tagName !== "SELECT") e.preventDefault(); });
    popup.addEventListener("click", function (e) {
      var btn = e.target.closest("button");
      if (!btn) return;
      if (btn.dataset.nav) { view.setMonth(view.getMonth() + +btn.dataset.nav); render(); }
      else if (btn.dataset.day) setValue(new Date(view.getFullYear(), view.getMonth(), +btn.dataset.day));
      else if (btn.dataset.action === "today") setValue(new Date());
      else if (btn.dataset.action === "clear") setValue(null);
      else close();
    });
    popup.addEventListener("change", function (e) {
      if (e.target.classList.contains("dp-month")) view.setMonth(+e.target.value);
      if (e.target.classList.contains("dp-year")) view.setFullYear(+e.target.value);
      render();
    });
    document.body.appendChild(popup);
    render();
    position();
  }

  function enhance(root) {
    (root || document).querySelectorAll("input[data-datepicker]:not([data-dp-ready])").forEach(function (el) {
      el.setAttribute("data-dp-ready", "");
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "dp-toggle";
      btn.title = "Open calendar";
      btn.setAttribute("aria-label", "Open calendar");
      btn.innerHTML = '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M4 0a.5.5 0 0 1 .5.5V1h7V.5a.5.5 0 0 1 1 0V1h1A1.5 1.5 0 0 1 15 2.5v12a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 1 14.5v-12A1.5 1.5 0 0 1 2.5 1h1V.5A.5.5 0 0 1 4 0zM2 5v9.5a.5.5 0 0 0 .5.5h11a.5.5 0 0 0 .5-.5V5H2z"/></svg>';
      btn.addEventListener("click", function () { if (input === el) close(); else open(el); });
      el.insertAdjacentElement("afterend", btn);
    });
  }

  document.addEventListener("focusin", function (e) {
    if (e.target.matches && e.target.matches("input[data-datepicker]")) open(e.target);
    else if (popup && !popup.contains(e.target)) close();
  });
  document.addEventListener("mousedown", function (e) {
    if (popup && !popup.contains(e.target) && e.target !== input && !e.target.closest(".dp-toggle")) close();
  });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" || e.key === "Tab" || e.key === "Enter") close(); });
  // Typing a date directly means the calendar is not needed; close it so it does not cover the form.
  document.addEventListener("input", function (e) { if (popup && e.isTrusted && e.target === input) close(); });
  window.addEventListener("resize", function () { if (popup) position(); });
  document.addEventListener("htmx:afterSwap", function (e) { enhance(e.target); });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { enhance(); });
  else enhance();
})();
