$(document).ready(function () {
    $(".datepicker").datepicker({
        format: "dd MM yyyy",
        autoclose: true,
        todayHighlight: true,
        weekStart: 1 // Monday
    });

    // Optional: Set today's date by default
    $(".datepicker").datepicker("setDate", new Date());

    
    $("#filterForm").on("submit", function (e) {
        e.preventDefault();
        const startDate = $("#startDate").datepicker("getDate").toISOString();
        const endDate = $("#endDate").datepicker("getDate").toISOString();

        console.log("Filtering data from", startDate, "to", endDate);

        $.ajax({
            url: "/analytics/dashboard",
            method: "POST",
            data: {
                start_date: startDate,
                end_date: endDate
            },
            success: function (data) {
                // Handle successful response (e.g., update table/chart)
                console.log("Data filtered successfully");
                updateTable(data.table_data);
            },
            error: function (err) {
                // Handle error
                console.error("Error filtering data:", err);
            }   
        });
    });
});

function updateTable(data) {
    const tbody = $("#salesTable tbody");
    tbody.empty();
    data.forEach(row => {
        const tr = `<tr>
            <td>${row.month}</td>
            <td>${row.product_name}</td>
            <td>${row.total_quantity}</td>
            <td>${row.total_revenue.toFixed(2)} UAH</td>
        </tr>`;
        tbody.append(tr);
    });
}

const datasets = products.map(p => ({
    label: p,
    data: chartData[p],
    borderWidth: 2,
    fill: false,
    tension: 0.3
}));

// new Chart(document.getElementById('salesChart'), {
//     type: 'line',
//     data: {
//         labels: months,
//         datasets: datasets
//     },
//     options: {
//         responsive: true,
//         plugins: {
//             title: {
//                 display: true,
//                 text: 'Monthly Product Revenue (UAH)'
//             },
//             legend: {
//                 position: 'bottom'
//             }
//         },
//         scales: {
//             y: {
//                 beginAtZero: true,
//                 title: { display: true, text: 'Revenue (UAH)' }
//             }
//         }
//     }
// });