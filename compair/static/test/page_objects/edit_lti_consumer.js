var EditLTIConsumerPage = function() {
    this.getLocation = function(id) {
        return 'lti/consumer/'+id+'/edit';
    };
};

module.exports = EditLTIConsumerPage;
