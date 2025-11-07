$(document).ready(function () {
  const $monthPicker = $("#monthPicker");
  const $tableBody = $("#statsTable tbody");

  $monthPicker.on("change", function () {
    const month = $(this).val(); // e.g. "2025-11"
    if (!month) return;

    $.ajax({
      url: `/analytics/get_monthly_stats`,
      method: "POST",
      data: JSON.stringify({ month: month }),
      contentType: "application/json",
      beforeSend: function () {
        $tableBody.html(
          `<tr><td colspan="8">Loading data for ${month}...</td></tr>`
        );
      },
      success: function (data) {
        $tableBody.empty();

        if (!data || data.length === 0) {
          $tableBody.html(
            `<tr><td colspan="8">No data available for ${month}</td></tr>`
          );
          return;
        }

        $.each(data, function (_, day) {
          const row = `
            <tr>
              <td>${day.date}</td>
              <td>${day.order_count}</td>
              <td>${day.total_sales.toFixed(2)}</td>
              <td>${day.total_margin.toFixed(2)}</td>
              <td><input class="form-control smmStats" type="number" step="0.1" data-type="spends" data-date="${day.date}" value="${day.smm_spends.toFixed(2)}"></td>
              <td><input class="form-control smmStats" type="number" step="0.1" data-type="coverage" data-date="${day.date}" value="${day.smm_coverage}"></td>
              <td><input class="form-control smmStats" type="number" step="0.1" data-type="clicks" data-date="${day.date}" value="${day.smm_clicks}"></td>
              <td><input class="form-control smmStats" type="number" step="0.1" data-type="direct_messages" data-date="${day.date}" value="${day.smm_direct_messages}"></td>
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
          const value = $(this).val();

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
            },
            error: function (xhr) {
              console.error("Failed to update:", xhr);
            }
          });
        });
      },
    });



  });
});
