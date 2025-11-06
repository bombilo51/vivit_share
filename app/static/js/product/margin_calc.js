console.log("Add Product JS loaded");

const costInput = document.getElementById('cost');
const marginPercentInput = document.getElementById('marginPercent');
const marginUAHInput = document.getElementById('marginUAH');
const marginMultiplierInput = document.getElementById('marginMultiplier');
const priceInput = document.getElementById('price');

function round(val) {
    return Math.round((val + Number.EPSILON) * 100) / 100;
}

function updatePriceFromMarginPercent() {
    const cost = parseFloat(costInput.value) || 0;
    const marginPercent = parseFloat(marginPercentInput.value) || 0;
    const marginUAH = round((marginPercent / 100) * cost);
    const marginMultiplier = round(1 + (marginPercent / 100));
    marginMultiplierInput.value = marginMultiplier;
    marginUAHInput.value = marginUAH;
    const price = round(cost + marginUAH);
    priceInput.value = price;
}

function updatePriceFromMarginUAH() {
    const cost = parseFloat(costInput.value) || 0;
    const marginUAH = parseFloat(marginUAHInput.value) || 0;
    const marginPercent = cost ? round((marginUAH / cost) * 100) : 0;
    const marginMultiplier = round(1 + (marginPercent / 100));
    marginMultiplierInput.value = marginMultiplier;
    marginPercentInput.value = marginPercent;
    const price = round(cost + marginUAH);
    priceInput.value = price;
}

function updateMarginsFromPrice() {
    const cost = parseFloat(costInput.value) || 0;
    const price = parseFloat(priceInput.value) || 0;
    const marginUAH = round(price - cost);
    marginUAHInput.value = marginUAH;
    const marginPercent = cost ? round((marginUAH / cost) * 100) : 0;
    marginPercentInput.value = marginPercent;
    const marginMultiplier = round(1 + (marginPercent / 100));
    marginMultiplierInput.value = marginMultiplier;
}

function updatePriceFromMarginMultiplier() {
    const cost = parseFloat(costInput.value) || 0;
    const marginMultiplier = parseFloat(marginMultiplierInput.value) || 0;
    const marginPercent = round((marginMultiplier - 1) * 100);
    const marginUAH = round((marginPercent / 100) * cost);
    marginPercentInput.value = marginPercent;
    marginUAHInput.value = marginUAH;
    const price = round(cost + marginUAH);
    priceInput.value = price;
}

marginMultiplierInput.addEventListener('input', updatePriceFromMarginMultiplier);
marginPercentInput.addEventListener('input', updatePriceFromMarginPercent);
marginUAHInput.addEventListener('input', updatePriceFromMarginUAH);
priceInput.addEventListener('input', updateMarginsFromPrice);