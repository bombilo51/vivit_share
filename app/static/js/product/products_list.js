function deleteProduct(id) {
    if (confirm("Are you sure you want to delete this product?")) {
        fetch(`delete_product/${id}`, {
            method: "DELETE",
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === "success") {
                    const row = document.getElementById(`productRow${id}`);
                    row.remove();
                    console.log("Product deleted successfully.");
                } else {
                    console.log("Error deleting product: " + data.message);
                }
            })
            .catch(error => {
                console.error("Error:", error);
                alert("An error occurred while deleting the product.");
            });
    }
}

$(function () {
    const $form = $("form[method='get']");
    const $container = $("#productsContainer");

    function loadIntoContainer(url, push = true) {
        $.ajax({
            url: url,
            method: "GET",
            headers: {"X-Requested-With": "XMLHttpRequest"},
            success: function (html) {
                $container.html(html);

                // Optional: update browser URL so back/forward works
                if (push) {
                    window.history.pushState({}, "", url);
                }
            },
            error: function () {
                // Fallback: if anything goes wrong, do a normal navigation
                window.location.href = url;
            }
        });
    }

    // 1) Filter form submit (no page reload)
    $form.on("submit", function (e) {
        e.preventDefault();

        // Reset to page 1 when applying filters
        const baseUrl = $form.attr("action") || window.location.pathname;
        const qs = $form.serialize(); // includes q, min_price, max_price, per_page, etc.
        const url = qs ? `${baseUrl}?${qs}` : baseUrl;

        loadIntoContainer(url);
    });

    // 2) Sorting + pagination clicks inside container (delegated)
    $container.on("click", "a.js-sort, a.js-page", function (e) {
        e.preventDefault();
        const url = $(this).attr("href");
        loadIntoContainer(url);
    });

    // 3) Back/forward browser navigation
    window.addEventListener("popstate", function () {
        loadIntoContainer(window.location.href, false);
    });

    const $searchField = $("#name-q");
    const $perPage = $('#per_page');

    $perPage.on("input", function (e) {
        e.preventDefault()
        $form.trigger('submit');
    });

    $searchField.on("input", function (e) {
        e.preventDefault()
        $form.trigger('submit');
    });

});
