async function fetchWorkRaveData() {
    try {
        const response = await fetch('workrave_stats.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching WorkRave data:', error);
        // You might want a more specific error message here for production
        document.body.innerHTML = "<p style='text-align: center; color: red;'>Failed to load WorkRave data. Please ensure 'workrave_stats.json' is correctly deployed.</p>";
        return [];
    }
}
