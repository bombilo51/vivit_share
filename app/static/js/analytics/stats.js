$(document).ready(function () {
    const $startDate = $("#startDateFilter");
    const $endDate = $("#endDateFilter");
    const $tableBody = $("#statsTable tbody");

    $startDate.datepicker({
        format: "yyyy-mm-dd",
        autoclose: true,
        todayHighlight: true,
        weekStart: 1, // Monday
        minViewMode: 0,
    });

    $endDate.datepicker({
        format: "yyyy-mm-dd",
        autoclose: true,
        todayHighlight: true,
        weekStart: 1, // Monday
        minViewMode: 0,
    });

  function DateFilterChange() {
      const startDate = $startDate.val();
      const endDate = $endDate.val();
      if (!startDate || !endDate) return;

    $.ajax({
      url: `/analytics/get_monthly_stats`,
      method: "POST",
      data: JSON.stringify({
          startDate: startDate,
          endDate: endDate,
      }),
      contentType: "application/json",
      beforeSend: function () {
        $tableBody.html(
          `<tr><td colspan="8">Loading data for ${startDate} - ${endDate}...</td></tr>`
        );
      },
      success: function (data) {
        $tableBody.empty();

        if (!data || data.length === 0) {
          $tableBody.html(
            `<tr><td colspan="8">No data available for ${startDate} - ${endDate}</td></tr>`
          );
          return;
        }

        $.each(data,
            function (_, day) {
          const row = `
            <tr>
              <td>${day.date}</td>
              <td>${day.order_count}</td>
              <td>${day.total_sales.toFixed(2)}</td>
              <td id="margin-${day.date}" value="${day.total_margin.toFixed(2)}">${day.total_margin.toFixed(2)}</td>
              <td><input id="spends-usd-${day.date}" class="form-control smmStats" type="number" data-type="spends" data-date="${day.date}" value="${day.smm_spends_usd.toFixed(2)}"></td>
              <td><input id="spends-uah-${day.date}" class="form-control smmStats" type="number" data-date="${day.date}" value="${day.smm_spends_uah.toFixed(2)}" disabled></td>
              <td><input class="form-control smmStats" type="number" step="0.1" data-type="coverage" data-date="${day.date}" value="${day.smm_coverage}"></td>
              <td><input class="form-control smmStats" type="number" step="0.1" data-type="clicks" data-date="${day.date}" value="${day.smm_clicks}"></td>
              <td><input class="form-control smmStats" type="number" step="0.1" data-type="direct_messages" data-date="${day.date}" value="${day.smm_direct_messages}"></td>
              <td><input id="revenue-${day.date}" class="form-control smmStats" type="number" step="0.1" data-type="revenue" data-date="${day.date}" value="${day.revenue}" readonly></td>
            </tr>
          `;
          $tableBody.append(row);
        });
      },
      error: function (xhr) {
        console.error(xhr);
        $tableBody.html(
          `<tr><td colspan="8" style="color:red;">Error loading data</td></tr>`
        );
      },
      complete: function () {
        $(".smmStats").on("change", function () {
          const type = $(this).data("type");
          const date = $(this).data("date");
          let value = $(this).val();
          const $revenue = $(`#revenue-${date}`);
          const $margin = $(`#margin-${date}`);
          const $spends = $(`#spends-usd-${date}`);
          const $spends_uah = $(`#spends-uah-${date}`);

          console.log($revenue);
          console.log($margin.text());
          console.log($spends);

          console.log(`CHANGED ${type} ${date} ${value}`)

          $.ajax({
            url: "/analytics/update_smm_stat",
            method: "POST",
            data: JSON.stringify({
              type: type,
              date: date,
              value: value
            }),
            contentType: "application/json",
            success: function (response) {
              console.log("Updated successfully:", response);

              let spends_uah = $spends.val() * parseFloat(response.usd_rate);
              $spends_uah.val(spends_uah);

              let revenue = parseFloat($margin.text()) - $spends_uah.val();
              $revenue.val(revenue);
            },
            error: function (xhr) {
              console.error("Failed to update:", xhr);
            }
          });
        });
      },
    });
  }

  $startDate.on("change", DateFilterChange);
  $endDate.on("change", DateFilterChange);
});
