from flask import Flask, render_template, request, jsonify
import grpc
import glossary_pb2
import glossary_pb2_grpc

app = Flask(__name__)


def get_glossary_stub():
    channel = grpc.insecure_channel('glossary-service:50051')
    return glossary_pb2_grpc.GlossaryServiceStub(channel)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/terms')
def get_all_terms():
    try:
        stub = get_glossary_stub()
        response = stub.GetAllTerms(glossary_pb2.Empty())
        terms = [{
            'term': term.term,
            'definition': term.definition,
            'category': term.category,
            'examples': term.examples
        } for term in response.terms]
        return jsonify(terms)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/terms/<term_name>')
def get_term(term_name):
    try:
        stub = get_glossary_stub()
        response = stub.GetTerm(glossary_pb2.TermRequest(term=term_name))
        if response.term:
            return jsonify({
                'term': response.term,
                'definition': response.definition,
                'category': response.category,
                'examples': response.examples
            })
        else:
            return jsonify({'error': 'Термин не найден'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search')
def search_terms():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    try:
        stub = get_glossary_stub()
        response = stub.SearchTerms(glossary_pb2.SearchRequest(query=query))
        terms = [{
            'term': term.term,
            'definition': term.definition,
            'category': term.category,
            'examples': term.examples
        } for term in response.terms]
        return jsonify(terms)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/terms', methods=['POST'])
def add_term():
    try:
        data = request.json
        stub = get_glossary_stub()
        response = stub.AddTerm(glossary_pb2.AddTermRequest(
            term=data['term'],
            definition=data['definition'],
            category=data.get('category', 'general'),
            examples=data.get('examples', '')
        ))
        return jsonify({
            'success': response.success,
            'message': response.message
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)