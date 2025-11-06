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