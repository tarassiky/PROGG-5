from concurrent import futures
import logging
import grpc
import glossary_pb2
import glossary_pb2_grpc
from glossary import Glossary


class GlossaryServicer(glossary_pb2_grpc.GlossaryServiceServicer):
    def __init__(self):
        self.glossary = Glossary()

    def GetTerm(self, request, context):
        term_data = self.glossary.get_term(request.term)
        if term_data:
            return glossary_pb2.TermResponse(
                term=term_data['term'],
                definition=term_data['definition'],
                category=term_data['category'],
                examples=term_data.get('examples', '')
            )
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Термин '{request.term}' не найден")
            return glossary_pb2.TermResponse()

    def SearchTerms(self, request, context):
        results = self.glossary.search_terms(request.query)
        response = glossary_pb2.SearchResponse()
        for term_data in results:
            response.terms.append(
                glossary_pb2.TermResponse(
                    term=term_data['term'],
                    definition=term_data['definition'],
                    category=term_data['category'],
                    examples=term_data.get('examples', '')
                )
            )
        return response

    def GetAllTerms(self, request, context):
        all_terms = self.glossary.get_all_terms()
        response = glossary_pb2.AllTermsResponse()
        for term_data in all_terms:
            response.terms.append(
                glossary_pb2.TermResponse(
                    term=term_data['term'],
                    definition=term_data['definition'],
                    category=term_data['category'],
                    examples=term_data.get('examples', '')
                )
            )
        return response

    def AddTerm(self, request, context):
        success, message = self.glossary.add_term(
            request.term,
            request.definition,
            request.category,
            request.examples
        )
        return glossary_pb2.OperationResponse(
            success=success,
            message=message
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    glossary_pb2_grpc.add_GlossaryServiceServicer_to_server(GlossaryServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Glossary gRPC Server started on port 50051")
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    serve()