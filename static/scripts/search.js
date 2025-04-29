
// Function to send a DELETE request for an item and remove its card from the DOM on success.
async function deleteItem(itemId, cardElement) {
    try {
    const response = await fetch(`/api/clothing/${itemId}`, {
        method: 'DELETE'
    });
    const result = await response.json();
    if (response.ok) {
        cardElement.remove();
    } else {
        alert(result.error || 'Failed to delete item.');
    }
    } catch (error) {
    console.error('Error deleting item:', error);
    }
}

// Function to render search results with delete buttons.
function renderItems(items) {
    const resultsDiv = document.querySelector('.search-results');
    resultsDiv.innerHTML = '';
    
    if (items.length > 0) {
    items.forEach(item => {
        const itemCard = document.createElement('div');
        itemCard.className = 'item-card';
        itemCard.dataset.itemId = item.item_id;  // store the id on the card

        const imageContent = item.item_image 
        ? `<img src="data:image/png;base64,${item.item_image}" alt="${item.item_name}">`
        : '<div class="no-image">No Image Available</div>';

        itemCard.innerHTML = `
        <div class="item-image">${imageContent}</div>
        <h3 class="item-name">${item.item_name}</h3>
        `;
        
        // Create and append the delete button.
        const deleteBtn = document.createElement('button');
        deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>'; // Font Awesome icon
        deleteBtn.className = 'delete-button';
        deleteBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to delete this item?')) {
            deleteItem(item.item_id, itemCard);
        }
        });
        itemCard.appendChild(deleteBtn);
        
        resultsDiv.appendChild(itemCard);
    });
    } else {
    resultsDiv.innerHTML = '<p class="no-results">No items found matching your search</p>';
    }
}

// Function to load clothing items (either all or filtered)
async function loadItems(event) {
    event.preventDefault();
    const formData = new URLSearchParams(new FormData(event.target));
    try {
    const response = await fetch(`/api/clothing?${formData}`);
    const items = await response.json();
    renderItems(items);
    } catch (error) {
    console.error('Error:', error);
    }
}

// Attach event listener to the search form.
document.querySelector('.search-form').addEventListener('submit', loadItems);

// Additionally, listen for input changes on the search text field.
document.querySelector('#item_name').addEventListener('input', async (e) => {
    const formData = new URLSearchParams(new FormData(document.querySelector('.search-form')));
    try {
    const response = await fetch(`/api/clothing?${formData}`);
    const items = await response.json();
    renderItems(items);
    } catch (error) {
    console.error('Error:', error);
    }
});

// Load all items on page load.
window.addEventListener('DOMContentLoaded', async () => {
    try {
    const response = await fetch('/api/clothing');
    const items = await response.json();
    renderItems(items);
    } catch (error) {
    console.error('Error:', error);
    }
});

// Filter toggle functionality
document.querySelector('.filter-toggle').addEventListener('click', () => {
    document.querySelector('.filters').classList.add('active');
    document.querySelector('.overlay').style.display = 'block';
    document.body.classList.add('overlay-active');
});

// Close filters when clicking overlay
document.querySelector('.overlay').addEventListener('click', () => {
    document.querySelector('.filters').classList.remove('active');
    document.querySelector('.overlay').style.display = 'none';
    document.body.classList.remove('overlay-active');
});

// Update clear and apply buttons
const applyButton = document.querySelector('#apply-filters');
applyButton.addEventListener('click', () => {
    document.querySelector('.filters').classList.remove('active');
    document.querySelector('.overlay').style.display = 'none';
    document.body.classList.remove('overlay-active');
});

const clearButton = document.querySelector('#clear-filters');
const filterInputs = document.querySelectorAll('.filters input[type="checkbox"]');
clearButton.addEventListener('click', () => {
    filterInputs.forEach(input => input.checked = false);
    document.querySelector('.filters').classList.remove('active');
    document.querySelector('.overlay').style.display = 'none';
    document.body.classList.remove('overlay-active');
});

