$(function () {
    const $startDate = $("#startDateFilter");
    const $endDate = $("#endDateFilter");
    const $tableBody = $("#statsTable tbody");

    let lastData = [];

    $startDate.datepicker({
        format: "yyyy-mm-dd",
        autoclose: true,
        todayHighlight: true,
        weekStart: 1,
        minViewMode: 0,
    });

    $endDate.datepicker({
        format: "yyyy-mm-dd",
        autoclose: true,
        todayHighlight: true,
        weekStart: 1,
        minViewMode: 0,
    });

    function DateFilterChange() {
        const startDate = $startDate.val();
        const endDate = $endDate.val();
        if (!startDate || !endDate) return;

        $.ajax({
            url: "/analytics/get_monthly_stats_html",
            method: "POST",
            data: JSON.stringify({startDate, endDate}),
            contentType: "application/json",
            beforeSend: function () {
                $tableBody.html(`<tr><td colspan="10">Loading data for ${startDate} - ${endDate}...</td></tr>`);
            },
            success: function (resp) {
                const html = resp?.html || "";
                const data = resp?.data || [];

                if (!data.length) {
                    $tableBody.html(`<tr><td colspan="10">No data available for ${startDate} - ${endDate}</td></tr>`);
                    lastData = [];
                    recountSum(lastData);
                    return;
                }

                $tableBody.html(html);
                lastData = data;
                recountSum(lastData);
            },
            error: function () {
                $tableBody.html(`<tr><td colspan="10" style="color:red;">Error loading data</td></tr>`);
            }
        });
    }

    $startDate.on("change", DateFilterChange);
    $endDate.on("change", DateFilterChange);

    $("#statsTable").on("change", ".smmStats", function () {
        const type = $(this).data("type");
        const date = $(this).data("date");
        const valueRaw = $(this).val();

        const d = String(date).replace(/-/g, "_");

        const $revenue = $(`#revenue-${d}`);
        const $margin = $(`#margin-${d}`);
        const $spendsUsd = $(`#spends-usd-${d}`);
        const $spendsUah = $(`#spends-uah-${d}`);

        $.ajax({
            url: "/analytics/update_smm_stat",
            method: "POST",
            data: JSON.stringify({type, date, value: valueRaw}),
            contentType: "application/json",
            success: function (response) {
                const usd = parseFloat($spendsUsd.val()) || 0;
                const rate = parseFloat(response.usd_rate) || 0;
                const spendsUAH = usd * rate;

                $spendsUah.text(moneySpace(spendsUAH, 2));

                const margin = $margin.data("value") || 0;
                const revenue = margin - spendsUAH;
                $revenue.text(moneySpace(revenue, 2));

                // sync model
                const row = lastData?.find(x => x.date === date);
                if (row) {
                    if (type === "spends") {
                        row.smm_spends_usd = usd;
                        row.smm_spends_uah = spendsUAH;
                        row.revenue = revenue;
                    } else if (type === "coverage") {
                        row.smm_coverage = parseFloat(valueRaw) || 0;
                    } else if (type === "clicks") {
                        row.smm_clicks = parseFloat(valueRaw) || 0;
                    } else if (type === "direct_messages") {
                        row.smm_direct_messages = parseFloat(valueRaw) || 0;
                    }
                }

                recountSum(lastData);
            }
        });
    });
});

function moneySpace(value, decimals = 2) {
    const num = Number(value) || 0;
    return new Intl.NumberFormat("uk-UA", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    }).format(num);
}

function recountSum(data) {
    const $day = $("#sum-day");
    const $orders = $("#sum-orders-count");
    const $sales = $("#sum-sales");
    const $margin = $("#sum-margin");
    const $spendsUSD = $("#sum-spends-usd");
    const $spendsUAH = $("#sum-spends-uah");
    const $coverage = $("#sum-coverage");
    const $clicks = $("#sum-clicks");
    const $dms = $("#sum-dms");
    const $revenue = $("#sum-revenue");

    let ordersCount = 0.0;
    let sales = 0.0;
    let margin = 0.0;
    let spendsUSD = 0.0;
    let spendsUAH = 0.0;
    let coverage = 0.0;
    let clicks = 0.0;
    let dms = 0.0;
    let revenue = 0.0;

    $.each(data, function (_, day) {
        ordersCount += day.order_count;
        sales += day.total_sales;
        margin += day.total_margin;
        spendsUSD += day.smm_spends_usd;
        spendsUAH += day.smm_spends_uah;
        coverage += day.smm_coverage;
        clicks += day.smm_clicks;
        dms += day.smm_direct_messages;
        revenue += day.revenue;
    });

    $day.text("За період");
    $orders.text(ordersCount);
    $sales.text(moneySpace(sales, 2));
    $margin.text(moneySpace(margin, 2));
    $spendsUSD.text(moneySpace(spendsUSD, 2));
    $spendsUAH.text(moneySpace(spendsUAH, 2));
    $coverage.text(coverage);
    $clicks.text(clicks);
    $dms.text(dms);
    $revenue.text(moneySpace(revenue, 2));
}