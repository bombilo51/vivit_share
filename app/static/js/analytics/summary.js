$(document).ready(function () {
    const $startDate = $("#startDate");
    const $endDate = $("#endDate");

    $(".datepicker").datepicker({
        format: "yyyy-mm-dd",
        autoclose: true,
        weekStart: 1, // Monday
    });

    $startDate.datepicker("setDate", new Date(new Date().getFullYear(), new Date().getMonth(), 1));
    $endDate.datepicker("setDate", new Date());

    $(".datepicker").on("change", function () {
        console.log("ONCHANGE CALLED")
        const date = $(this).val(); // e.g. "2025-11"
        const startDate = $startDate.val();
        const endDate = $endDate.val();
        if (!date) return;

        $.ajax({
            url: `/analytics/summary`,
            method: "POST",
            data: JSON.stringify({
                startDate: startDate,
                endDate: endDate,
            }),
            contentType: "application/json",
            success: function (data) {
                console.log(`[SENT] From : ${startDate} To : ${endDate}`)
                console.log(`[RECEIVED] ${data}`)
                console.log(data)
                if (data.status === "error") {
                    $("#error-box").text(data.message)
                }
                else if (data.status === "success") {
                    $("#total_spends").text(data.total_spends);
                    $("#total_coverage").text(data.total_coverage);
                    $("#total_clicks").text(data.total_clicks);
                    $("#total_orders").text(data.total_orders);
                    $("#total_sales").text(data.total_sales);
                    $("#sum_sales").text(data.sum_sales);
                    $("#margin").text(data.margin);
                    $("#revenue").text(data.revenue);
                    $("#convert").text(data.convert + " %");
                    $("#roas").text(data.roas);
                    $("#order_price_average").text(data.order_price_average);
                }


            },
            error: function (xhr) {
                console.error(xhr);
            },
        });
    });
});
