// Script to load all clothing items into scroll bar
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/api/clothing');
        const items = await response.json();
        const scrollBar = document.querySelector('.scroll-bar');
        items.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'draggable-item';
            itemDiv.dataset.itemId = item.item_id;
            let html = '';
            if (item.item_image) {
            html += `<img src="data:image/png;base64,${item.item_image}" alt="${item.item_name}" width="100">`;
            }
            html += `<p>${item.item_name}</p>`;
            itemDiv.innerHTML = html;
            scrollBar.appendChild(itemDiv);
        });
        initDraggables();
    } catch (error) {
        console.error('Error loading items:', error);
    }
});

// Script to generate random outfit
document.querySelector('.generate-btn').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/outfit/random'); // Fetch random outfit from the API
        const outfit = await response.json();
        const canvas = document.querySelector('.outfit-canvas');
        const scrollBar = document.querySelector('.scroll-bar');

        // Return all items in the canvas back to the scroll bar
        Array.from(canvas.children).forEach((item) => {
            resetPosition(item);
        });

        // Define the display order and positions for the items
        const order = ['tops', 'bottoms', 'shoes', 'outerwear', 'bracelet', 'necklace', 'earrings', 'ring'];
        const positions = [
            { left: 500, top: 25 }, // Position for tops
            { left: 500, top: 225 }, // Position for bottoms
            { left: 500, top: 425 }, // Position for shoes
            { left: 250, top: 225 }, // Position for outerwear
            { left: 700, top: 225 },  // Position for bracelet
            { left: 850, top: 25 }, // Position for necklace
            { left: 700, top: 25 }, // Position for earrings
            { left: 850, top: 225 }  // Position for ring
        ];

        // Loop through the categories and add items to the canvas
        order.forEach((category, index) => {
            const item = outfit[category];
            if (item) {
                // Find the corresponding item in the scroll bar
                const itemInScrollBar = scrollBar.querySelector(`.draggable-item[data-item-id="${item.item_id}"]`);
            if (itemInScrollBar) {
                // Remove the item from the scroll bar
                scrollBar.removeChild(itemInScrollBar);
            }

            // Create the HTML content for the item
            const itemDiv = document.createElement('div');
            itemDiv.className = 'draggable-item'; // Add draggable and in-canvas classes
            itemDiv.dataset.itemId = item.item_id;

            let html = ``;
            if (item.item_image) {
                html += `<img src="data:image/png;base64,${item.item_image}" alt="${item.item_name}" width="100">`;
            }
            html += `<p>${item.item_name}</p>`;
            itemDiv.innerHTML = html;

            // Position the item in the canvas
            itemDiv.style.position = 'absolute';
            itemDiv.style.left = `${positions[index].left}px`;
            itemDiv.style.top = `${positions[index].top}px`;

            // Append the item to the canvas
            canvas.appendChild(itemDiv);
            }
        });
    } catch (error) {
        console.error('Error generating outfit:', error);
    }
});

// Script to clear the canvas and return items back to scroll bar
document.querySelector('.clear-btn').addEventListener('click', () => {
    const canvas = document.querySelector('.outfit-canvas');
    const scrollBar = document.querySelector('.scroll-bar');

    // Return all items in the canvas back to the scroll bar
    Array.from(canvas.children).forEach((item) => {
        console.log("hi");
        resetPosition(item);
    });
});

// Script to save the outfit
document.querySelector('.save-btn').addEventListener('click', async () => {
    try {
        const canvas = document.querySelector('.outfit-canvas');
        const outfitItems = Array.from(canvas.children).map(item => {
            return {
                item_id: item.dataset.itemId,
                position: {
                    x: parseFloat(item.style.left),
                    y: parseFloat(item.style.top)
                }
            };
        });

        if (outfitItems.length === 0) {
            alert('Please add items to the canvas before saving!');
            return;
        }
        const outfitName = document.getElementById('outfit-name').value;
        if (outfitName === "") {
            alert('Please name the outfit before saving!');
            return;
        }

        const response = await fetch('/api/outfits', {
            method: 'POST',
            headers: {
            'Content-Type': 'application/json',
            },
            body: JSON.stringify({
            name: document.getElementById('outfit-name').value,
            items: outfitItems
            })
        });

        if (response.ok) {
            alert('Outfit saved successfully!');
        } else {
            alert('Failed to save outfit');
        }
    } catch (error) {
        console.error('Error saving outfit:', error);
        alert('Error saving outfit');
    }
});

// Script to initialize draggable items
let originalParent = null;
let originalPosition = null;
let originalScroll = null;
function initDraggables() {
    interact('.draggable-item').draggable({
        modifiers: [
            interact.modifiers.restrictRect({
            restriction: 'body',
            endOnly: true
            })
        ],
        listeners: {
            start(event) {
                const target = event.target;
                // Store original position
                originalParent = target.parentNode;
                originalScroll = {
                    x: originalParent.scrollLeft,
                    y: originalParent.scrollTop
                };
                
                // Make item position fixed during drag
                target.style.position = 'fixed';
                target.style.zIndex = '10000';
                target.style.width = `${target.offsetWidth}px`;
                
                // Get position relative to parent including scroll
                const rect = target.getBoundingClientRect();
                const parentRect = originalParent.getBoundingClientRect();
                
                originalPosition = {
                    x: rect.left - parentRect.left + originalParent.scrollLeft,
                    y: rect.top - parentRect.top + originalParent.scrollTop
                };
                
                // Get current dimensions after setting fixed width
                const width = target.offsetWidth;
                const height = target.offsetHeight;
                
                // Calculate centered position based on mouse coordinates
                const startX = event.clientX - width / 2;
                const startY = event.clientY - height / 2;
                
                // Set initial position and update data attributes
                target.style.left = `${startX}px`;
                target.style.top = `${startY}px`;
                target.dataset.x = startX;
                target.dataset.y = startY;
            },
            move(event) {
                const target = event.target;
                // Update position during drag
                const x = (parseFloat(target.dataset.x) || 0) + event.dx;
                const y = (parseFloat(target.dataset.y) || 0) + event.dy;
                
                target.style.left = `${x}px`;
                target.style.top = `${y}px`;
                target.dataset.x = x;
                target.dataset.y = y;
            },
            end(event) {
                const target = event.target;
                const canvas = document.querySelector('.outfit-canvas');
                const canvasRect = canvas.getBoundingClientRect();
                const targetRect = target.getBoundingClientRect();

                // Check if the item is outside the canvas
                const isOutsideCanvas =
                    targetRect.right < canvasRect.left ||
                    targetRect.left > canvasRect.right ||
                    targetRect.bottom < canvasRect.top ||
                    targetRect.top > canvasRect.bottom;
                console.log('isOutsideCanvas:', isOutsideCanvas);
                if (isOutsideCanvas || !target.classList.contains('in-canvas')) {
                    resetPosition(target); // Reset position if outside canvas
                }
            }
        }
    });

    // Enable dropzone on the canvas
    interact('.outfit-canvas').dropzone({
        accept: '.draggable-item',
        ondrop: (event) => {
            const canvas = event.target;
            const target = event.relatedTarget;
            const canvasRect = canvas.getBoundingClientRect();
            
            // Convert fixed position to canvas-relative
            const x = parseFloat(target.style.left) - canvasRect.left;
            const y = parseFloat(target.style.top) - canvasRect.top;
            
            // Position in canvas
            target.style.position = 'absolute';
            target.style.left = `${x}px`;
            target.style.top = `${y}px`;
            target.style.zIndex = 'auto';
            target.classList.add('in-canvas');
            
            // Append to canvas
            canvas.appendChild(target);
        }
    });
}

// Return itme to scroll bar
function resetPosition(target) {
    // Return item to original position
    target.style.position = 'relative'; 
    target.style.width = 'auto';
    target.style.zIndex = 'auto';
    target.style.transform = 'none';  // Reset transform

    // Append the item back to the clothing list
    const scrollBar = document.querySelector('.scroll-bar');
    scrollBar.appendChild(target);

    // Restore scroll position first
    scrollBar.scrollTo(0, 0);

    // Use requestAnimationFrame to ensure proper positioning
    requestAnimationFrame(() => {
        target.style.left = `0px`;
        target.style.top = `0px`;
    });
}
