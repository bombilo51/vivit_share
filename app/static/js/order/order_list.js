$(function () {
    const $form = $("form[method='get']");
    const $container = $("#ordersContainer");
    const $unit = $("#unitNamesSelect");
    const $datepicker = $(".datepicker");

    $datepicker.datepicker({
        format: "yyyy-mm-dd", // ISO-friendly format
        autoclose: true,
        todayHighlight: true,
        weekStart: 1, // Monday
    });

    function buildUrlFromForm() {
        const baseUrl = $form.attr("action") || window.location.pathname;
        const qs = $form.serialize(); // includes repeated unit_names
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
                window.location.href = url; // safe fallback
            }
        });
    }

    function submitFiltersResetPage() {
        // reset page on any filter change
        // (we do it by removing page param: easiest is just rely on backend default page=1)
        // But if you ever add <input name="page">, set it to 1 here.
        loadIntoContainer(buildUrlFromForm(), true);
    }

    // Intercept full form submit (Enter key etc.)
    $form.on("submit", function (e) {
        e.preventDefault();
        submitFiltersResetPage();
    });

    // Sorting + pagination clicks (delegated)
    $container.on("click", "a.js-sort, a.js-page", function (e) {
        e.preventDefault();
        loadIntoContainer($(this).attr("href"), true);
    });

    // Back/forward
    window.addEventListener("popstate", function () {
        loadIntoContainer(window.location.href, false);
    });

    // Auto-submit when regular inputs change (order_id/start/end/per_page)
    $form.on("change", "input, select", function (e) {
        // ignore select2 internal triggers; handle unit via select2 events below
        if (this.id === "unitNamesSelect") return;
        submitFiltersResetPage();
    });

    // Select2 init + auto-submit on select/unselect
    if ($unit.length) {
        $unit.select2({
            theme: "bootstrap-5",
            width: "100%",
            closeOnSelect: true,
            placeholder: "Почніть вводити назву…",
            ajax: {
                url: "/order/unit_names",
                dataType: "json",
                delay: 200,
                data: function (params) {
                    return {
                        term: params.term || "",
                        "selected[]": $unit.val() || [],
                        start: $form.find("[name='start']").val() || "",
                        end: $form.find("[name='end']").val() || "",
                        order_id: $form.find("[name='order_id']").val() || ""
                    };
                },
                processResults: function (data) {
                    return data;
                }
            }
        });

        $unit.on("select2:select select2:unselect", function () {
            submitFiltersResetPage();
        });
    }
});