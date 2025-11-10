$(document).ready(function () {

    $("#orderDate").datepicker({
        format: "yyyy-mm-dd", // ISO-friendly format
        autoclose: true,
        todayHighlight: true,
        weekStart: 1, // Monday
    });

    if ($("#orderDate").val() == '') {
        $("#orderDate").datepicker("setDate", new Date());
    }
    
    const $tableBody = $('#orderItemsBody');
    const $grandTotal = $('#grandTotal');

    const round = (n) => Math.round((n + Number.EPSILON) * 100) / 100;

    function recalculateRow($row) {
        const quantity = parseFloat($row.find('.quantity-input').val()) || 0;
        const price = parseFloat($row.find('.unit-price-input').val()) || 0;
        console.log('Recalculating row:', quantity, price);
        const total = round(quantity * price);
        $row.find('.total-price-input').val(total ? round(total).toFixed(2) : '');
    }

    function recalculateUnitPrice($row) {
        const total = parseFloat($row.find('.total-price-input').val()) || 0;
        const quantity = parseFloat($row.find('.quantity-input').val()) || 0;
        console.log('Recalculating unit price:', total, quantity);
        const price = quantity > 0 ? round(total / quantity) : 0;
        $row.find('.unit-price-input').val(price ? round(price).toFixed(2) : '');
    }

    function recalculateGrandTotal() {
        let grandTotal = 0;
        console.log('Recalculating grand total');
        $tableBody.find('.total-price-input').each(function () {
            grandTotal += parseFloat($(this).val()) || 0;
        });
        $grandTotal.text(round(grandTotal).toFixed(2));
    }

    function addNewRow() {
        const $templateRow = $tableBody.find('.orderItemRow:first');
        const $newRow = $templateRow.clone();

        $newRow.find('input').val('');
        $newRow.find('.product-select').val('').trigger('change');
        $newRow.find('.remove-item-btn').removeClass('d-none');

        $tableBody.append($newRow);
    }

    function maybeAddNewRow($row) {
        const product = $row.find('.product-select').val();
        const quantity = parseFloat($row.find('.quantity-input').val()) || 0;
        const $rows = $tableBody.find('.orderItemRow');
        const isLastRow = $row.is($rows.last());

        if (product && quantity > 0 && isLastRow) addNewRow();
    }

    $tableBody.on('change', '.product-select', function () {
        const $row = $(this).closest('.orderItemRow');
        const price = parseFloat($(this).find('option:selected').data('price')) || 0;
        $row.find('.unit-price-input').val(price ? round(price).toFixed(2) : '');
        $row.find('.quantity-input').val(price ? '1' : '');
        recalculateRow($row);
        recalculateGrandTotal();
        maybeAddNewRow($row);
    });

    $tableBody.on('input', '.quantity-input, .unit-price-input', function () {
        const $row = $(this).closest('.orderItemRow');
        recalculateRow($row);
        recalculateGrandTotal();
        maybeAddNewRow($row);
    });

    $tableBody.on('input', '.total-price-input', function () {
        const $row = $(this).closest('.orderItemRow');
        recalculateUnitPrice($row);
        recalculateGrandTotal();
        maybeAddNewRow($row);
    });

    $tableBody.on('click', '.remove-item-btn', function () {
        const $row = $(this).closest('.orderItemRow');
        $row.remove();
        recalculateGrandTotal();
    });
});
