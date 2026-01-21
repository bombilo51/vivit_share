$(function () {
    const $form = $("form[method='get']");
    const $container = $("#ordersContainer");

    const $input = $("#unitNameInput");
    const $suggest = $("#unitNameSuggest");
    const $selected = $("#selectedUnitNames");

    const $datepicker = $('.datepicker');

    $datepicker.datepicker({
        format: "yyyy-mm-dd", // ISO-friendly format
        autoclose: true,
        todayHighlight: true,
        weekStart: 1, // Monday
    });

    $datepicker.on("changeDate", function () {
        $("form[method='get']").trigger("submit");
    });

    // --- existing helpers you already use ---
    function buildUrlFromForm() {
        const baseUrl = $form.attr("action") || window.location.pathname;
        const qs = $form.serialize(); // includes repeated unit_names via hidden inputs
        return qs ? `${baseUrl}?${qs}` : baseUrl;
    }

    function loadIntoContainer(url, push = true) {
        $.ajax({
            url: url,
            method: "GET",
            headers: {"X-Requested-With": "XMLHttpRequest"},
            success: function (html) {
                $container.html(html);
                if (push) window.history.pushState({}, "", url);
            },
            error: function () {
                window.location.href = url;
            }
        });
    }

    function submitFiltersResetPage() {
        loadIntoContainer(buildUrlFromForm(), true);
    }

    // --- generic auto-submit for other fields ---
    $form.on("change", "input, select", function () {
        if (this.id === "unitNameInput") return;
        submitFiltersResetPage();
    });

    $form.on("submit", function (e) {
        e.preventDefault();
        submitFiltersResetPage();
    });

    $container.on("click", "a.js-sort, a.js-page", function (e) {
        e.preventDefault();
        loadIntoContainer($(this).attr("href"), true);
    });

    window.addEventListener("popstate", function () {
        loadIntoContainer(window.location.href, false);
    });

    // --- unit name token logic ---
    function getSelectedValues() {
        const vals = [];
        $selected.find("span[data-value]").each(function () {
            vals.push($(this).data("value"));
        });
        return vals;
    }

    function hasSelected(value) {
        return getSelectedValues().includes(value);
    }

    function addToken(value) {
        value = (value || "").trim();
        if (!value) return;
        if (hasSelected(value)) return;

        const $pill = $(`
      <span class="badge bg-primary d-inline-flex align-items-center gap-2 py-2 px-2" data-value="${$("<div>").text(value).html()}">
        <span></span>
        <button type="button" class="btn-close btn-close-white btn-sm js-remove-unit" aria-label="Remove"></button>
      </span>
    `);
        $pill.find("span").text(value);

        $selected.append($pill);
        $("#unitNamesHiddenInputs").append(
            `<input type="hidden" name="unit_names" value="${$("<div>").text(value).html()}">`
        );
        $input.val("");
        hideSuggest();
        submitFiltersResetPage();
    }

    function removeToken(value) {
        $selected.find(`span[data-value="${CSS.escape(value)}"]`).remove();
        $("#unitNamesHiddenInputs")
            .find(`input[type="hidden"][name="unit_names"][value="${CSS.escape(value)}"]`)
            .remove();
        submitFiltersResetPage();
    }

    $selected.on("click", ".js-remove-unit", function () {
        const value = $(this).closest("span[data-value]").data("value");
        removeToken(value);
    });

    // --- suggestions ---
    let suggestXhr = null;

    function hideSuggest() {
        $suggest.addClass("d-none").empty();
    }

    function showSuggest(items) {
        if (!items || items.length === 0) return hideSuggest();

        $suggest.empty();
        items.forEach((name) => {
            const $a = $(`<button type="button" class="list-group-item list-group-item-action"></button>`);
            $a.text(name);
            $a.attr("data-value", name);
            $suggest.append($a);
        });

        $suggest.removeClass("d-none");
    }

    function fetchSuggest(term) {
        if (suggestXhr) suggestXhr.abort();

        const selected = getSelectedValues();
        const data = {
            term: term || "",
            "selected[]": selected,
            start: $form.find("[name='start']").val() || "",
            end: $form.find("[name='end']").val() || "",
            order_id: $form.find("[name='order_id']").val() || ""
        };

        suggestXhr = $.ajax({
            url: "/order/unit_names",
            method: "GET",
            dataType: "json",
            data: data,
            success: function (resp) {
                showSuggest(resp.items || []);
            },
            error: function () {
                hideSuggest();
            }
        });
    }

    // Type -> suggest (debounced)
    let t = null;
    $input.on("input", function () {
        const term = $input.val().trim();
        clearTimeout(t);
        if (!term) return hideSuggest();

        t = setTimeout(() => fetchSuggest(term), 200);
    });

    // Enter adds current highlighted/first suggestion if present; otherwise do nothing
    $input.on("keydown", function (e) {
        if (e.key === "Enter") {
            e.preventDefault();

            const $first = $suggest.find("[data-value]").first();
            if ($first.length) {
                addToken($first.attr("data-value"));
            }
        } else if (e.key === "Escape") {
            hideSuggest();
        }
    });

    // Click suggestion to add
    $suggest.on("click", "[data-value]", function () {
        addToken($(this).attr("data-value"));
    });

    // Hide dropdown when clicking outside
    $(document).on("click", function (e) {
        const inside = $(e.target).closest("#unitNameInput, #unitNameSuggest, #selectedUnitNames").length > 0;
        if (!inside) hideSuggest();
    });

});
