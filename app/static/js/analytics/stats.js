$(document).ready(function () {
    const $startDate = $("#startDateFilter");
    const $endDate = $("#endDateFilter");
    const $tableBody = $("#statsTable tbody");

    $startDate.datepicker({
        format: "yyyy-mm-dd", autoclose: true, todayHighlight: true, weekStart: 1, // Monday
        minViewMode: 0,
    });

    $endDate.datepicker({
        format: "yyyy-mm-dd", autoclose: true, todayHighlight: true, weekStart: 1, // Monday
        minViewMode: 0,
    });

    function DateFilterChange() {
        const startDate = $startDate.val();
        const endDate = $endDate.val();
        if (!startDate || !endDate) return;

        $.ajax({
            url: `/analytics/get_monthly_stats`,
            method: "POST",
            data: JSON.stringify({startDate, endDate}),
            contentType: "application/json",
            beforeSend: function () {
                $tableBody.html(`<tr><td colspan="10">Loading data for ${startDate} - ${endDate}...</td></tr>`);
            },
            success: function (data) {
                $tableBody.empty();

                if (!data || data.length === 0) {
                    $tableBody.html(`<tr><td colspan="10">No data available for ${startDate} - ${endDate}</td></tr>`);
                    return;
                }

                lastData = data;

                $.each(data, function (_, day) {
                    const row = `
            <tr>
              <td>${day.date}</td>
              <td>${day.order_count}</td>
              <td>${Number(day.total_sales || 0).toFixed(2)}</td>
              <td id="margin-${day.date}">${Number(day.total_margin || 0).toFixed(2)}</td>
              <td><input id="spends-usd-${day.date}" class="form-control smmStats" type="number" data-type="spends" data-date="${day.date}" value="${Number(day.smm_spends_usd || 0).toFixed(2)}"></td>
              <td><input id="spends-uah-${day.date}" class="form-control" type="number" data-date="${day.date}" value="${Number(day.smm_spends_uah || 0).toFixed(2)}" disabled></td>
              <td><input class="form-control smmStats" type="number" step="0.1" data-type="coverage" data-date="${day.date}" value="${Number(day.smm_coverage || 0)}"></td>
              <td><input class="form-control smmStats" type="number" step="0.1" data-type="clicks" data-date="${day.date}" value="${Number(day.smm_clicks || 0)}"></td>
              <td><input class="form-control smmStats" type="number" step="0.1" data-type="direct_messages" data-date="${day.date}" value="${Number(day.smm_direct_messages || 0)}"></td>
              <td><input id="revenue-${day.date}" class="form-control" type="number" step="0.1" data-date="${day.date}" value="${Number(day.revenue || 0).toFixed(2)}" readonly></td>
            </tr>
          `;
                    $tableBody.append(row);
                });

                recountSum(lastData);
            },
            error: function () {
                $tableBody.html(`<tr><td colspan="10" style="color:red;">Error loading data</td></tr>`);
            }
        });
    }

    $startDate.on("change", DateFilterChange);
    $endDate.on("change", DateFilterChange);

    // Bind once (delegated)
    $("#statsTable").on("change", ".smmStats", function () {
        const type = $(this).data("type");
        const date = $(this).data("date");
        const valueRaw = $(this).val();

        const $revenue = $(`#revenue-${date}`);
        const $margin = $(`#margin-${date}`);
        const $spendsUsd = $(`#spends-usd-${date}`);
        const $spendsUah = $(`#spends-uah-${date}`);

        $.ajax({
            url: "/analytics/update_smm_stat",
            method: "POST",
            data: JSON.stringify({type, date, value: valueRaw}),
            contentType: "application/json",
            success: function (response) {
                const usd = parseFloat($spendsUsd.val()) || 0;
                const rate = parseFloat(response.usd_rate) || 0;
                const spendsUAH = usd * rate;

                $spendsUah.val(spendsUAH.toFixed(2));

                const margin = parseFloat($margin.text()) || 0;
                const revenue = margin - spendsUAH;
                $revenue.val(revenue.toFixed(2));

                // keep model + totals in sync
                const row = lastData?.find(x => x.date === date);
                if (row) {
                    if (type === "spends") {
                        row.smm_spends_usd = usd;
                        row.smm_spends_uah = spendsUAH;
                        row.revenue = revenue;
                    } else if (type === "coverage") row.smm_coverage = parseFloat(valueRaw) || 0; else if (type === "clicks") row.smm_clicks = parseFloat(valueRaw) || 0; else if (type === "direct_messages") row.smm_direct_messages = parseFloat(valueRaw) || 0;
                }
                recountSum(lastData);
            }
        });
    });
});

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

    $day.text("За період")
    $orders.text(ordersCount)
    $sales.text(sales.toFixed(2))
    $margin.text(margin.toFixed(2))
    $spendsUSD.text(spendsUSD.toFixed(2))
    $spendsUAH.text(spendsUAH.toFixed(2))
    $coverage.text(coverage)
    $clicks.text(clicks)
    $dms.text(dms)
    $revenue.text(revenue.toFixed(2))
}