/**
 * Helper functions for formatting job descriptions and other text
 */

/**
 * Format text with preserved line breaks and paragraphs
 * @param {string} text - The text to format
 * @returns {string} - HTML formatted text
 */
function formatText(text) {
    if (!text) return '';
    
    // Split by double newlines to get paragraphs
    var paragraphs = text.split('\n\n');
    var formattedText = '';
    
    for (var i = 0; i < paragraphs.length; i++) {
        // Replace single newlines with <br> tags
        var paragraph = paragraphs[i].replace(/\n/g, '<br>');
        formattedText += '<p>' + paragraph + '</p>';
    }
    
    return formattedText;
}

/**
 * Detect bullet points and format them as lists
 * @param {string} text - The text to format
 * @returns {string} - HTML formatted text with proper lists
 */
function formatBulletPoints(text) {
    if (!text) return '';
    
    // Replace bullet points with HTML list items
    var formattedText = text.replace(/- (.*?)(?=\n|$)/g, '<li>$1</li>');
    
    // Wrap consecutive list items in <ul> tags
    formattedText = formattedText.replace(/<li>.*?<\/li>(?:\s*<li>.*?<\/li>)*/g, function(match) {
        return '<ul>' + match + '</ul>';
    });
    
    return formattedText;
}

/**
 * Format date to include day of week
 * @param {string} dateString - The date string in format YYYY-MM-DD
 * @returns {string} - Formatted date with day of week
 */
function formatDateWithDayOfWeek(dateString) {
    if (!dateString) return '';
    
    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return dateString; // Return original if invalid
        
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const dayOfWeek = days[date.getDay()];
        
        // Format: DayOfWeek, YYYY-MM-DD
        return dayOfWeek + ', ' + dateString;
    } catch (e) {
        console.error('Error formatting date:', e);
        return dateString; // Return original on error
    }
}

/**
 * Convert markdown to HTML
 * @param {string} markdown - The markdown text
 * @returns {string} - HTML formatted text
 */
function markdownToHtml(markdown) {
    if (!markdown) return '';
    
    // Process headers
    let html = markdown
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^# (.*$)/gm, '<h1>$1</h1>');
    
    // Process lists
    html = html.replace(/^\* (.*$)/gm, '<ul><li>$1</li></ul>')
               .replace(/^- (.*$)/gm, '<ul><li>$1</li></ul>');
    
    // Fix multiple consecutive list items
    html = html.replace(/<\/ul>\s*<ul>/g, '');
    
    // Process paragraphs
    const paragraphs = html.split(/\n\s*\n/);
    html = paragraphs.map(p => {
        if (p.trim() === '') return '';
        if (p.startsWith('<h') || p.startsWith('<ul>')) return p;
        return `<p>${p}</p>`;
    }).join('');
    
    // Process bold and italic
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
               .replace(/\*(.*?)\*/g, '<em>$1</em>')
               .replace(/__(.*?)__/g, '<strong>$1</strong>')
               .replace(/_(.*?)_/g, '<em>$1</em>');
    
    // Process links
    html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>');
    
    // Process line breaks
    html = html.replace(/\n/g, '<br>');
    
    return html;
}
