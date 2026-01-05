$(function () {

    $('.searchable-select').select2({
        placeholder: 'Оберіть Товар',
        theme: 'bootstrap-5',
        allowClear: false,
        width: '100%'
    });

    const $orderDate = $("#orderDate");

    $orderDate.datepicker({
        format: "yyyy-mm-dd", // ISO-friendly format
        autoclose: true,
        todayHighlight: true,
        weekStart: 1, // Monday
    });

    if ($orderDate.val() === '') {
        $orderDate.datepicker("setDate", new Date());
    }

    const $tableBody = $('#orderItemsBody');
    const $grandTotal = $('#grandTotal');

    const round = (n) => Math.round((n + Number.EPSILON) * 100) / 100;

    function recalculateRow($row) {
        const quantity = parseFloat($row.find('.quantity-input').val()) || 0;
        const price = parseFloat($row.find('.unit-price-input').val()) || 0;
        const unit_margin = parseFloat($row.find('.unit-margin-input').val()) || 0;
        console.log('Recalculating row:', quantity, price, unit_margin);
        const total = round(quantity * price);
        const total_margin = unit_margin * quantity;
        $row.find('.total-price-input').val(total ? round(total).toFixed(2) : '');
        $row.find('.total-margin-input').val(total_margin ? round(total_margin).toFixed(2) : '');
    }

    function recalculateGrandMargin() {
        let grandMargin = 0;
        $tableBody.find('.total-margin-input').each(function () {
            grandMargin += parseFloat($(this).val()) || 0;
        });
        $('#grandMargin').text(round(grandMargin).toFixed(2))
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
        recalculateGrandMargin();
    }

    function addNewRow() {
        const $templateRow = $tableBody.find('.orderItemRow:first');

        $templateRow.find('.product-select').select2('destroy');

        const $newRow = $templateRow.clone();

        $newRow.find('input').val('');
        $newRow.find('.product-select').val('');
        $newRow.find('.remove-item-btn').removeClass('d-none');

        $tableBody.append($newRow);

        // Re-init template row
        $templateRow.find('.product-select').select2({
            placeholder: 'Оберіть Товар',
            theme: 'bootstrap-5',
            allowClear: false,
            width: '100%'
        });

        // Init new row only
        $newRow.find('.product-select').select2({
            placeholder: 'Оберіть Товар',
            theme: 'bootstrap-5',
            allowClear: false,
            width: '100%'
        });
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
        const margin = parseFloat($(this).find('option:selected').data('margin')) || 0;
        $row.find('.unit-price-input').val(price ? round(price).toFixed(2) : '');
        $row.find('.quantity-input').val(price ? '1' : '');
        $row.find('.unit-margin-input').val(margin ? margin : '');
        $row.find('.total-margin-input').val(margin ? margin : '');
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

    const $rows = $(".orderItemRow .quantity-input")

    $rows.trigger('input');

    console.log($rows)


});
