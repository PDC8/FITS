async function loadFriends() {
  try {
    const response = await fetch('/api/friends');
    const friends = await response.json();
    const container = document.getElementById('friends-list-container');
    
    container.innerHTML = friends.map(friend => `
        <div class="friend-item" data-user-id="${friend.user_id}">
          <span class="friend-name">${friend.netid}</span>
          <div class="icon-btn remove-btn" data-user-id="${friend.user_id}">
            <i class="fas fa-user-minus remove-icon"></i>
          </div>
        </div>
    `).join('');
    
    // Add click event listeners to friend items
    container.querySelectorAll('.friend-item').forEach(item => {
      item.addEventListener('click', async (e) => {
        // Don't trigger if clicking the remove button
        if (!e.target.closest('.remove-btn')) {
          const friendId = item.dataset.userId;
          await loadOutfits(friendId);
        }
      });
    });

    // Add search functionality
    document.getElementById('search-friends').addEventListener('input', (e) => {
      const searchTerm = e.target.value.toLowerCase();
      Array.from(container.children).forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(searchTerm) ? 'block' : 'none';
      });
    });

    // Add event listeners for "Remove" buttons
    container.querySelectorAll('.remove-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const friendId = btn.dataset.userId;
        try {
          const response = await fetch('/api/friends/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ friend_id: friendId })
          });

          if (response.ok) {
            btn.parentElement.remove(); // Remove the friend from the list
            loadAddFriendList(); // Refresh add friend list
          }
        } catch (error) {
          console.error('Error removing friend:', error);
        }
      });
    });
  } catch (error) {
    console.error('Error loading friends:', error);
  }
}

async function loadPendingRequests() {
  try {
    const response = await fetch('/api/friend-requests');
    const requests = await response.json();
    const container = document.getElementById('requests-list');
    const count = document.getElementById('pending-requests-count');
    const pendingRequests = document.getElementById('pending-requests');
    
    container.innerHTML = requests.map(request => `
        <div class="request-friend-item">
          <span class="friend-info">${request.netid}</span>
          <div class="icon-btns">
            <div class="icon-btn accept-btn" data-requester="${request.requester_id}">
              <i class="fas fa-user-plus add-icon"></i>
            </div>
            <div class="icon-btn reject-btn" data-requester="${request.requester_id}">
              <i class="fas fa-user-minus remove-icon"></i>
            </div>
          </div>
        </div>
    `).join('');
    
    
    // Show or hide the badge based on the number of pending requests
    if (requests.length > 0) {
      pendingRequests.classList.remove('hidden');
      count.textContent = requests.length;
      count.classList.add('show');
    } else {
      pendingRequests.classList.add('hidden');
      count.classList.remove('show');
    }

    // Add event listeners for accept buttons
    document.querySelectorAll('.accept-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const requesterId = btn.dataset.requester;
        try {
          const response = await fetch('/api/friends/accept', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ requester_id: requesterId })
          });
          if (response.ok) {
            loadPendingRequests();
            loadFriends(); // Refresh friends list
          }
        } catch (error) {
          console.error('Error accepting request:', error);
        }
      });
    });

    // Add event listeners for reject buttons
    container.querySelectorAll('.reject-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const requesterId = btn.dataset.requester;
        try {
          const response = await fetch('/api/friends/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ friend_id: requesterId })
          });

          if (response.ok) {
            loadPendingRequests();
            loadAddFriendList();
          }
        } catch (error) {
          console.error('Error removing friend:', error);
        }
      });
    });
  } catch (error) {
    console.error('Error loading requests:', error);
  }
}

async function loadAddFriendList() {
  try {
    // Fetch all users who are not already friends
    const response = await fetch('/api/users/not-friends');
    const users = await response.json();
    const searchResultsContainer = document.getElementById('search-results');

    // Display all users initially
    displayUsers(users, searchResultsContainer);

    // Add search functionality
    const searchInput = document.getElementById('friend-search-input');
    searchInput.addEventListener('input', () => {
      const searchTerm = searchInput.value.toLowerCase();
      const filteredUsers = users.filter(user =>
        user.netid.toLowerCase().includes(searchTerm)
      );
      displayUsers(filteredUsers, searchResultsContainer);
    });
  } catch (error) {
    console.error('Error loading add friend list:', error);
  }
}

function displayUsers(users, container) {
  container.innerHTML = '';
  if (users.length === 0) {
      container.innerHTML = '<p>No users found</p>';
      return;
  }

  users.forEach(user => {
      const userItem = document.createElement('div');
      userItem.classList.add('user-item');
      userItem.innerHTML = `
          <div class="add-friend-item">
              <span class="friend-info">${user.netid}</span>
              <div class="icon-btn add-btn" data-user-id="${user.user_id}">
                  <i class="fas fa-user-plus add-icon"></i>
              </div>
          </div>
      `;

    // Add event listener for the "Add" button
    userItem.querySelector('.add-btn').addEventListener('click', async () => {
      console.log(user);
      try {
        const response = await fetch('/api/friends', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ friend_id: user.user_id })
        });

        if (response.ok) {
          userItem.remove(); // Remove the user from the list after adding
        } else {
          document.getElementById('add-friend-message').textContent = 'Error sending friend request.';
        }
      } catch (error) {
        console.error('Error adding friend:', error);
        document.getElementById('add-friend-message').textContent = 'Error processing request.';
      }
    });

    container.appendChild(userItem);
  });
}

async function loadOutfits(userId) {
  try {
      console.log('Loading outfits for friend ID:', userId);
      const response = await fetch(`/api/outfits/${userId}`);
      if (!response.ok) {
          console.error('Failed to load outfits');
          return;
      }
      
      const outfits = await response.json();
      const container = document.getElementById('outfits-container');
      const isCurrentUser = userId == currentUserId;
      const heading = isCurrentUser ? "My Outfits" : `${document.querySelector(`[data-user-id="${userId}"] .friend-name`).textContent}'s Outfits`;

      container.innerHTML = `
          <div class="outfits-header">
            <i id="back-to-my-outfits" class="fas fa-arrow-left back-arrow" style="visibility: ${!isCurrentUser ? 'visible' : 'hidden'};"></i>
            <h2 class="outfits-heading">${heading}</h2>
          </div>
          <div class="outfits-container">
            ${outfits.map(outfit => `
              <div class="outfit-container">
                <h3>${outfit.outfit_name}</h3>
                <div class="outfit-canvas">
                  ${outfit.outfit_items.map(item => `
                    <div class="outfit-item" 
                      style="left: ${item.position_x + 60}px; 
                              top: ${item.position_y}px;">
                      ${item.item_image ? `<img src="data:image/png;base64,${item.item_image}" alt="${item.item_name}">` : ''}
                      <p>${item.item_name}</p>
                    </div>
                  `).join('')}
                </div>
              </div>
            `).join('')}
          </div>
      `;
      // Add event listener to the "Back to My Outfits" button
      if (!isCurrentUser) {
        const backArrow = document.getElementById('back-to-my-outfits');
        backArrow.addEventListener('click', () => {
          loadOutfits(currentUserId); // Load the current user's outfits
        });
      }
      container.classList.remove('hidden');
      container.scrollIntoView({ behavior: 'smooth' });

  } catch (error) {
      console.error('Error loading friend outfits:', error);
  }
}


// Initial load
loadFriends();
loadPendingRequests();
loadAddFriendList();
loadOutfits(currentUserId);